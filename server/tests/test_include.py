from pathlib import Path

from features.completion import build_completions_from_index
from features.definition import build_definitions_from_index
from parser import parse_document
from workspace_index import (
    WorkspaceIndex,
    expand_include_closure,
    extract_includes,
    resolve_entry_path,
    resolve_pool,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_include_directive():
    text = (FIXTURES / "include_main.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_extract_includes_from_source():
    text = '#include "facts.lp".\nbird(a).'
    assert extract_includes(text) == ["facts.lp"]


def test_resolve_entry_path_relative_to_active_file():
    uri = resolve_entry_path(
        "file:///proj/sub/main.lp",
        "facts.lp",
        ["/proj"],
    )
    assert uri == "file:///proj/sub/facts.lp"


def test_resolve_entry_path_falls_back_to_workspace_root():
    uri = resolve_entry_path(
        "file:///proj/sub/main.lp",
        "shared/facts.lp",
        ["/proj"],
    )
    # sub/shared/facts.lp does not exist in test; root fallback is attempted
    assert uri.endswith("shared/facts.lp")


def test_resolve_pool_expands_includes_when_additional_files_empty():
    main_uri = "file:///proj/main.lp"
    facts_uri = "file:///proj/facts.lp"
    texts = {
        main_uri: '#include "facts.lp".\nok :- bird(X).',
        facts_uri: "bird(tweety).",
    }

    pool = resolve_pool(
        active_uri=main_uri,
        workspace_roots=["/proj"],
        config_path=None,
        additional_files=[],
        discovered_uris=[main_uri, facts_uri, "file:///proj/other.lp"],
        get_text=lambda uri: texts.get(uri),
    )
    assert main_uri in pool
    assert facts_uri in pool
    assert "file:///proj/other.lp" not in pool


def test_expand_include_closure_is_transitive():
    a = "file:///proj/a.lp"
    b = "file:///proj/b.lp"
    c = "file:///proj/c.lp"
    texts = {
        a: '#include "b.lp".',
        b: '#include "c.lp".\npred(x).',
        c: "base(y).",
    }
    uris = expand_include_closure(
        [a],
        ["/proj"],
        lambda uri: texts.get(uri),
    )
    assert uris == {a, b, c}


def test_cross_file_nav_through_include():
    idx = WorkspaceIndex()
    idx.upsert("file:///main.lp", '#include "facts.lp".\nok :- bird(X).')
    idx.upsert("file:///facts.lp", "bird(tweety).")
    pool = ["file:///main.lp", "file:///facts.lp"]
    merged = idx.merged(pool)
    items = build_completions_from_index(merged)
    labels = {i.label for i in items}
    assert "bird/1" in labels

    doc_main = idx.merged(["file:///main.lp"])
    locs = build_definitions_from_index(
        merged,
        line=1,
        column=6,
        uri="file:///main.lp",
        document_index=doc_main,
    )
    assert any(l.uri == "file:///facts.lp" for l in locs)
