from unittest.mock import MagicMock

import server as srv
from workspace_index import WorkspaceIndex


def test_merged_cache_returns_same_object_on_repeat_call():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "flies(X) :- bird(X).")
    uris = ["file:///a.lp", "file:///b.lp"]
    first = idx.merged(uris)
    second = idx.merged(uris)
    assert first is second


def test_upsert_invalidates_merged_cache_for_affected_uri():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "flies(X) :- bird(X).")
    uris = ["file:///a.lp", "file:///b.lp"]
    cached = idx.merged(uris)
    idx.upsert("file:///a.lp", "bird(tweety).\nzebra(1).")
    refreshed = idx.merged(uris)
    assert cached is not refreshed
    assert ("zebra", 1) in refreshed


def test_upsert_does_not_invalidate_unrelated_cache_entry():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "flies(X) :- bird(X).")
    idx.upsert("file:///c.lp", "zebra(1).")
    ab = idx.merged(["file:///a.lp", "file:///b.lp"])
    idx.upsert("file:///c.lp", "zebra(2).")
    ab_after = idx.merged(["file:///a.lp", "file:///b.lp"])
    assert ab is ab_after


def test_remove_invalidates_merged_cache():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    uris = ["file:///a.lp"]
    cached = idx.merged(uris)
    idx.remove("file:///a.lp")
    refreshed = idx.merged(uris)
    assert cached is not refreshed
    assert refreshed == {}


def test_refresh_workspace_scan_indexes_only_new_files(monkeypatch, tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    existing = root / "old.lp"
    existing.write_text("old(x).", encoding="utf-8")
    new_file = root / "new.lp"
    new_file.write_text("new(y).", encoding="utf-8")

    monkeypatch.setattr(srv, "WORKSPACE", WorkspaceIndex())
    monkeypatch.setattr(srv, "WORKSPACE_ROOTS", [str(root)])
    monkeypatch.setattr(srv, "DISCOVERED", [existing.resolve().as_uri()])
    monkeypatch.setattr(srv, "ADDITIONAL_FILES", None)
    srv.WORKSPACE.upsert(existing.resolve().as_uri(), existing.read_text(encoding="utf-8"))

    upsert_calls: list[str] = []
    original_upsert = srv.WORKSPACE.upsert

    def tracking_upsert(uri: str, text: str) -> None:
        upsert_calls.append(uri)
        original_upsert(uri, text)

    monkeypatch.setattr(srv.WORKSPACE, "upsert", tracking_upsert)

    srv._refresh_workspace_scan(None)

    new_uri = new_file.resolve().as_uri()
    assert new_uri in upsert_calls
    assert existing.resolve().as_uri() not in upsert_calls


def test_refresh_workspace_scan_removes_stale_index_entries(monkeypatch, tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    kept = root / "kept.lp"
    kept.write_text("kept(x).", encoding="utf-8")
    stale_uri = "file:///proj/removed.lp"

    monkeypatch.setattr(srv, "WORKSPACE", WorkspaceIndex())
    monkeypatch.setattr(srv, "WORKSPACE_ROOTS", [str(root)])
    monkeypatch.setattr(srv, "DISCOVERED", [stale_uri])
    monkeypatch.setattr(srv, "ADDITIONAL_FILES", None)
    srv.WORKSPACE.upsert(stale_uri, "removed(x).")

    srv._refresh_workspace_scan(None)

    assert not srv.WORKSPACE.has(stale_uri)
    assert srv.WORKSPACE.has(kept.resolve().as_uri())


def test_workspace_symbol_skips_refresh_when_discovery_clean(monkeypatch):
    calls: list[str] = []

    def fake_refresh(ls):
        calls.append("refresh")

    monkeypatch.setattr(srv, "_refresh_workspace_scan", fake_refresh)
    monkeypatch.setattr(srv, "_discovery_dirty", False)
    monkeypatch.setattr(srv, "DISCOVERED", [])
    monkeypatch.setattr(srv, "WORKSPACE", WorkspaceIndex())

    ls = MagicMock()
    srv.workspace_symbol(ls, MagicMock(query=""))

    assert calls == []


def test_ensure_discovery_refreshes_when_dirty(monkeypatch):
    calls: list[str] = []

    def fake_refresh(ls):
        calls.append("refresh")

    monkeypatch.setattr(srv, "_refresh_workspace_scan", fake_refresh)
    monkeypatch.setattr(srv, "_discovery_dirty", True)

    srv._ensure_discovery(None)

    assert calls == ["refresh"]
    assert srv._discovery_dirty is False
