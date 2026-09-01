from pathlib import Path

from lsprotocol.types import SymbolKind

from workspace_index import WorkspaceIndex
from features.workspace_symbols import build_workspace_symbols


def test_workspace_symbols_lists_predicates_across_files(tmp_path: Path):
    a = (tmp_path / "a.lp").resolve()
    b = (tmp_path / "b.lp").resolve()
    a.write_text("bird(tweety).\n", encoding="utf-8")
    b.write_text("flies(X) :- bird(X).\n", encoding="utf-8")
    idx = WorkspaceIndex()
    idx.upsert(a.as_uri(), a.read_text(encoding="utf-8"))
    idx.upsert(b.as_uri(), b.read_text(encoding="utf-8"))
    merged = idx.merged([a.as_uri(), b.as_uri()])

    symbols = build_workspace_symbols(merged, "")
    names = sorted(s.name for s in symbols)
    assert names == ["bird/1", "flies/1"]


def test_workspace_symbols_location_prefers_definition():
    idx = WorkspaceIndex()
    uri = "file:///test.lp"
    text = "bird(tweety).\nflies(X) :- bird(X)."
    idx.upsert(uri, text)
    merged = idx.merged([uri])

    bird = next(s for s in build_workspace_symbols(merged, "") if s.name == "bird/1")
    assert bird.kind == SymbolKind.Function
    assert bird.location.uri == uri
    assert bird.location.range.start.line == 0
    assert bird.location.range.start.character == 0


def test_workspace_symbols_query_filters_case_insensitive():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).\nzebra(1).")
    merged = idx.merged(["file:///a.lp"])

    symbols = build_workspace_symbols(merged, "BIR")
    assert [s.name for s in symbols] == ["bird/1"]


def test_workspace_symbols_empty_index():
    assert build_workspace_symbols({}, "") == []
