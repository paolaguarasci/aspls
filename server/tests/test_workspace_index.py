from workspace_index import WorkspaceIndex, resolve_pool


def test_resolve_pool_uses_additional_files_when_present():
    pool = resolve_pool(
        active_uri="file:///proj/main.lp",
        workspace_roots=["/proj"],
        config_path="/proj/aspls.clingo.json",
        additional_files=["facts.lp"],
        discovered_uris=[
            "file:///proj/main.lp",
            "file:///proj/facts.lp",
            "file:///proj/other.lp",
        ],
    )
    assert "file:///proj/main.lp" in pool
    assert "file:///proj/facts.lp" in pool
    assert "file:///proj/other.lp" not in pool


def test_resolve_pool_falls_back_to_discovered():
    discovered = ["file:///proj/a.lp", "file:///proj/b.lp"]
    pool = resolve_pool(
        active_uri="file:///proj/a.lp",
        workspace_roots=["/proj"],
        config_path=None,
        additional_files=None,
        discovered_uris=discovered,
    )
    assert pool == discovered


def test_merged_index_unions_predicates_across_files():
    idx = WorkspaceIndex()
    idx.upsert("file:///a.lp", "bird(tweety).")
    idx.upsert("file:///b.lp", "flies(X) :- bird(X).")
    merged = idx.merged()
    assert ("bird", 1) in merged
    assert ("flies", 1) in merged
    uris = {o.uri for o in merged[("bird", 1)]}
    assert uris == {"file:///a.lp", "file:///b.lp"}
