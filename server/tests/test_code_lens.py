from features.code_lens import build_code_lenses_from_index
from workspace_index import WorkspaceIndex


def _titles(uri: str, merged) -> list[tuple[int, str]]:
    lenses = build_code_lenses_from_index(uri, merged)
    return [(l.range.start.line, l.command.title) for l in lenses if l.command]


def test_occurrence_count_single_file():
    idx = WorkspaceIndex()
    uri = "file:///main.lp"
    idx.upsert(uri, "bird(tweety).\nflies(X) :- bird(X).")
    merged = idx.merged()
    titles = _titles(uri, merged)
    assert (0, "Run this file") in titles
    assert (0, "2 occurrences") in titles


def test_occurrence_count_cross_file():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "ok :- bird(X).")
    merged = idx.merged()
    titles = _titles("file:///a.lp", merged)
    assert (0, "2 occurrences") in titles


def test_rule_body_only_no_lenses():
    idx = WorkspaceIndex()
    uri = "file:///b.lp"
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert(uri, ":- bird(X).")
    merged = idx.merged()
    assert build_code_lenses_from_index(uri, merged) == []


def test_singular_occurrence_label():
    idx = WorkspaceIndex()
    uri = "file:///solo.lp"
    idx.upsert(uri, "lonely.")
    merged = idx.merged()
    titles = _titles(uri, merged)
    assert (0, "1 occurrence") in titles


def test_show_references_command_arguments():
    idx = WorkspaceIndex()
    uri = "file:///main.lp"
    idx.upsert(uri, "bird(tweety).")
    merged = idx.merged()
    lenses = build_code_lenses_from_index(uri, merged)
    ref_lens = next(l for l in lenses if l.command and "occurrence" in l.command.title)
    assert ref_lens.command.command == "aspls.codeLens.showReferences"
    assert ref_lens.command.arguments == [uri, 0, 0]
