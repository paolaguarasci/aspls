from features.completion import build_completions_from_index
from features.definition import build_definitions_from_index
from features.hover import build_hover_from_index
from features.references import build_references_from_index
from workspace_index import WorkspaceIndex


def test_completion_includes_predicates_from_other_file():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "penguin(pingu).")
    items = build_completions_from_index(idx.merged())
    labels = {i.label for i in items}
    assert "bird/1" in labels and "penguin/1" in labels


def test_definition_returns_other_file_uri():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "ok :- bird(X).")
    # Cursor on bird in b.lp (0-based LSP: line 0, column 6)
    doc_b = idx.merged(["file:///b.lp"])
    locs = build_definitions_from_index(
        idx.merged(),
        line=0,
        column=6,
        uri="file:///b.lp",
        document_index=doc_b,
    )
    assert any(l.uri == "file:///a.lp" for l in locs)


def test_cursor_resolves_active_file_when_line_column_collide():
    """Critical: merged find_key_at must not pick another file's predicate.

    alpha/1 in a.lp and beta/1 in b.lp both sit at (line 1, column 1). Cursor
    in B must resolve beta, not alpha.
    """
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "alpha(x).")
    idx.upsert("file:///b.lp", "beta(y).")
    merged = idx.merged()
    doc_b = idx.merged(["file:///b.lp"])

    locs = build_definitions_from_index(
        merged, line=0, column=0, uri="file:///b.lp", document_index=doc_b
    )
    assert len(locs) == 1
    assert locs[0].uri == "file:///b.lp"
    assert locs[0].range.start.character == 0

    refs = build_references_from_index(
        merged, line=0, column=0, uri="file:///b.lp", document_index=doc_b
    )
    assert len(refs) == 1
    assert refs[0].uri == "file:///b.lp"

    hover = build_hover_from_index(
        merged, line=0, column=0, uri="file:///b.lp", document_index=doc_b
    )
    assert hover is not None
    assert "beta/1" in hover.contents.value
    assert "alpha/1" not in hover.contents.value
