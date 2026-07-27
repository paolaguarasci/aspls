import json
from pathlib import Path

from lsprotocol.types import FileChangeType, FileEvent

from features.diagnostics import build_diagnostics
from server import is_config_file_change
from workspace_index import resolve_pool


def _once_used_msgs(diags):
    return [d.message for d in diags if "used only once" in d.message]


def test_is_config_file_change_matches_basename():
    assert is_config_file_change(
        "file:///proj/aspls.clingo.json",
        "aspls.clingo.json",
    )


def test_is_config_file_change_rejects_other_files():
    assert not is_config_file_change(
        "file:///proj/other.json",
        "aspls.clingo.json",
    )


def test_is_config_file_change_respects_custom_name():
    assert is_config_file_change(
        "file:///proj/my-clingo.json",
        "my-clingo.json",
    )
    assert not is_config_file_change(
        "file:///proj/aspls.clingo.json",
        "my-clingo.json",
    )


def test_watched_changes_detect_relevant_config_event():
    import server as srv

    changes = [
        FileEvent(uri="file:///proj/readme.md", type=FileChangeType.Changed),
        FileEvent(uri="file:///proj/aspls.clingo.json", type=FileChangeType.Changed),
    ]
    assert any(is_config_file_change(c.uri, "aspls.clingo.json") for c in changes)
    assert not any(is_config_file_change(c.uri, "aspls.clingo.json") for c in changes[:1])


def test_config_file_change_realigns_once_used(tmp_path: Path, monkeypatch):
    """Editing aspls.clingo.json must change pool-dependent onceUsed without restart."""
    import server as srv

    root = tmp_path
    main = root / "main.lp"
    other = root / "other.lp"
    main.write_text("bird(tweety).\n", encoding="utf-8")
    other.write_text("flies(X) :- bird(X).\n", encoding="utf-8")
    config = root / "aspls.clingo.json"
    config.write_text(json.dumps({"additionalFiles": []}), encoding="utf-8")

    monkeypatch.setattr(srv, "WORKSPACE_ROOTS", [str(root)])
    monkeypatch.setattr(srv, "CONFIG_FILE_NAME", "aspls.clingo.json")
    monkeypatch.setattr(srv, "WORKSPACE", srv.WorkspaceIndex())
    monkeypatch.setattr(srv, "DISCOVERED", [])
    monkeypatch.setattr(srv, "ADDITIONAL_FILES", None)

    assert is_config_file_change(config.resolve().as_uri(), "aspls.clingo.json")

    srv._refresh_workspace_scan(None)
    assert srv.ADDITIONAL_FILES == []

    main_uri = srv._path_to_uri(main)
    other_uri = srv._path_to_uri(other)
    pool = resolve_pool(
        active_uri=main_uri,
        workspace_roots=srv.WORKSPACE_ROOTS,
        config_path=None,
        additional_files=srv.ADDITIONAL_FILES,
        discovered_uris=srv.DISCOVERED,
    )
    assert pool == [main_uri]

    for uri in pool:
        text = Path(srv._uri_to_path(uri)).read_text(encoding="utf-8")
        srv.WORKSPACE.upsert(uri, text)
    merged = srv.WORKSPACE.merged(pool)
    main_text = main.read_text(encoding="utf-8")
    before = build_diagnostics(
        main_text,
        once_used=True,
        index=merged,
        document_uri=main_uri,
    )
    assert any("bird/1" in m for m in _once_used_msgs(before))

    # Simulate watched-file change: expand pool to include other.lp
    config.write_text(
        json.dumps({"additionalFiles": ["other.lp"]}),
        encoding="utf-8",
    )
    assert is_config_file_change(config.resolve().as_uri(), srv.CONFIG_FILE_NAME)
    srv._refresh_workspace_scan(None)
    assert srv.ADDITIONAL_FILES == ["other.lp"]

    pool_after = resolve_pool(
        active_uri=main_uri,
        workspace_roots=srv.WORKSPACE_ROOTS,
        config_path=None,
        additional_files=srv.ADDITIONAL_FILES,
        discovered_uris=srv.DISCOVERED,
    )
    assert main_uri in pool_after and other_uri in pool_after
    for uri in pool_after:
        text = Path(srv._uri_to_path(uri)).read_text(encoding="utf-8")
        srv.WORKSPACE.upsert(uri, text)
    merged_after = srv.WORKSPACE.merged(pool_after)
    after = build_diagnostics(
        main_text,
        once_used=True,
        index=merged_after,
        document_uri=main_uri,
    )
    assert not any("bird/1" in m for m in _once_used_msgs(after))
