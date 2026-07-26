from pathlib import Path

from workspace_index import WorkspaceIndex
from features.workspace_predicates import build_workspace_predicate_nodes


def test_workspace_merges_predicates_across_files(tmp_path: Path):
    a = (tmp_path / "a.lp").resolve()
    b = (tmp_path / "b.lp").resolve()
    a.write_text("bird(tweety).\n", encoding="utf-8")
    b.write_text("flies(X) :- bird(X).\n", encoding="utf-8")
    idx = WorkspaceIndex()
    idx.upsert(a.as_uri(), a.read_text(encoding="utf-8"))
    idx.upsert(b.as_uri(), b.read_text(encoding="utf-8"))
    merged = idx.merged([a.as_uri(), b.as_uri()])
    nodes = build_workspace_predicate_nodes(merged, [str(tmp_path)])
    by_name = {n["name"]: n for n in nodes}
    assert "bird/1" in by_name
    bird = by_name["bird/1"]
    roles = [c["name"] for c in bird["children"]]
    assert "fact" in roles and "rule_body" in roles
    # leaves carry uri
    fact_occ = next(c for c in bird["children"] if c["name"] == "fact")["children"][0]
    assert fact_occ["uri"] == a.as_uri()
    assert "a.lp" in fact_occ["name"] or fact_occ["name"].endswith(":1") or ":1" in fact_occ["name"]


def test_workspace_empty_index():
    assert build_workspace_predicate_nodes({}, []) == []
