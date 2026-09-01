import re

from features.rename import build_prepare_rename_from_index, build_rename_edit_from_index
from workspace_index import WorkspaceIndex


def _apply_edits(text: str, edits) -> str:
    """Apply LSP TextEdits (0-based) to a single-line or multi-line string."""
    lines = text.split("\n")
    for edit in sorted(
        edits,
        key=lambda e: (e.range.start.line, e.range.start.character),
        reverse=True,
    ):
        start_line = edit.range.start.line
        start_char = edit.range.start.character
        end_line = edit.range.end.line
        end_char = edit.range.end.character
        if start_line == end_line:
            line = lines[start_line]
            lines[start_line] = line[:start_char] + edit.new_text + line[end_char:]
        else:
            prefix = lines[start_line][:start_char]
            suffix = lines[end_line][end_char:]
            lines[start_line : end_line + 1] = [prefix + edit.new_text + suffix]
    return "\n".join(lines)


def test_rename_all_occurrences_in_single_file():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    edit = build_rename_edit_from_index(
        _index(text, "file:///test.lp"),
        line=0,
        column=1,
        new_name="avian",
        uri="file:///test.lp",
        document_index=_index(text, "file:///test.lp"),
    )
    assert edit is not None
    edits = edit.changes["file:///test.lp"]
    assert len(edits) == 2
    new_text = _apply_edits(text, edits)
    assert "avian(tweety)" in new_text
    assert "bird(X)" not in new_text
    assert "avian(X)" in new_text
    assert "penguin(X)" in new_text


def test_rename_across_pool_files():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "flies(X) :- bird(X).")
    merged = idx.merged()
    doc_b = idx.merged(["file:///b.lp"])
    edit = build_rename_edit_from_index(
        merged,
        line=0,
        column=13,
        new_name="avian",
        uri="file:///b.lp",
        document_index=doc_b,
    )
    assert edit is not None
    assert set(edit.changes) == {"file:///a.lp", "file:///b.lp"}
    a_text = _apply_edits("bird(tweety).", edit.changes["file:///a.lp"])
    b_text = _apply_edits("flies(X) :- bird(X).", edit.changes["file:///b.lp"])
    assert a_text == "avian(tweety)."
    assert b_text == "flies(X) :- avian(X)."


def test_rename_includes_show_directive():
    text = "bird(tweety).\n#show bird/1."
    edit = build_rename_edit_from_index(
        _index(text, "file:///test.lp"),
        line=0,
        column=1,
        new_name="avian",
        uri="file:///test.lp",
        document_index=_index(text, "file:///test.lp"),
    )
    assert edit is not None
    new_text = _apply_edits(text, edit.changes["file:///test.lp"])
    assert new_text == "avian(tweety).\n#show avian/1."


def test_rename_invalid_new_name_returns_none():
    text = "bird(tweety)."
    edit = build_rename_edit_from_index(
        _index(text, "file:///test.lp"),
        line=0,
        column=1,
        new_name="Bird",
        uri="file:///test.lp",
        document_index=_index(text, "file:///test.lp"),
    )
    assert edit is None


def test_rename_over_non_predicate_returns_none():
    text = "bird(tweety)."
    edit = build_rename_edit_from_index(
        _index(text, "file:///test.lp"),
        line=10,
        column=0,
        new_name="avian",
        uri="file:///test.lp",
        document_index=_index(text, "file:///test.lp"),
    )
    assert edit is None


def test_prepare_rename_returns_predicate_name_range():
    text = "bird(tweety)."
    rng = build_prepare_rename_from_index(
        _index(text, "file:///test.lp"),
        line=0,
        column=1,
        uri="file:///test.lp",
        document_index=_index(text, "file:///test.lp"),
    )
    assert rng is not None
    assert rng.start.line == 0
    assert rng.start.character == 0
    assert rng.end.character == 4


def test_cursor_resolves_active_file_when_line_column_collide():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "alpha(x).")
    idx.upsert("file:///b.lp", "beta(y).")
    merged = idx.merged()
    doc_b = idx.merged(["file:///b.lp"])

    edit = build_rename_edit_from_index(
        merged,
        line=0,
        column=0,
        new_name="gamma",
        uri="file:///b.lp",
        document_index=doc_b,
    )
    assert edit is not None
    assert set(edit.changes) == {"file:///b.lp"}
    assert "file:///a.lp" not in edit.changes


def _index(text: str, uri: str):
    idx = WorkspaceIndex()
    idx.upsert(uri, text)
    return idx.merged([uri])
