from pathlib import Path

from features.completion import build_completions_from_index
from features.definition import build_definitions_from_index
from features.hover import build_hover_from_index
from features.references import build_references_from_index
from parser import parse_document
from workspace_index import (
    WorkspaceIndex,
    expand_include_closure,
    extract_includes,
    resolve_entry_path,
    resolve_pool,
)

FIXTURES = Path(__file__).parent / "fixtures"
INCLUDE_MAIN = FIXTURES / "include_main.lp"
INCLUDE_FACTS = FIXTURES / "include_facts.lp"


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


def _fixture_include_pool():
    """Load include fixtures from disk and build an indexed pool."""
    main_uri = INCLUDE_MAIN.resolve().as_uri()
    facts_uri = INCLUDE_FACTS.resolve().as_uri()
    workspace_root = str(FIXTURES.parent.parent.parent.resolve())

    texts = {
        main_uri: INCLUDE_MAIN.read_text(),
        facts_uri: INCLUDE_FACTS.read_text(),
    }

    pool = resolve_pool(
        active_uri=main_uri,
        workspace_roots=[workspace_root],
        config_path=None,
        additional_files=[],
        discovered_uris=[main_uri, facts_uri],
        get_text=lambda uri: texts.get(uri),
    )
    assert facts_uri in pool

    idx = WorkspaceIndex()
    for uri in pool:
        idx.upsert(uri, texts[uri])
    merged = idx.merged(pool)
    doc_main = idx.merged([main_uri])
    return main_uri, facts_uri, pool, merged, doc_main


def test_cross_file_nav_through_include():
    main_uri, facts_uri, pool, merged, doc_main = _fixture_include_pool()

    items = build_completions_from_index(merged)
    labels = {i.label for i in items}
    assert "bird/1" in labels

    # Cursor on bird in "ok :- bird(X)." (line 2, column 6)
    locs = build_definitions_from_index(
        merged,
        line=2,
        column=6,
        uri=main_uri,
        document_index=doc_main,
    )
    assert any(l.uri == facts_uri for l in locs)


def test_references_cross_file_through_include_fixture():
    main_uri, facts_uri, pool, merged, doc_main = _fixture_include_pool()

    refs = build_references_from_index(
        merged,
        line=2,
        column=6,
        uri=main_uri,
        document_index=doc_main,
    )
    uris = {r.uri for r in refs}
    assert main_uri in uris
    assert facts_uri in uris


def test_hover_cross_file_through_include_fixture():
    main_uri, facts_uri, pool, merged, doc_main = _fixture_include_pool()

    hover = build_hover_from_index(
        merged,
        line=2,
        column=6,
        uri=main_uri,
        document_index=doc_main,
    )
    assert hover is not None
    assert "bird/1" in hover.contents.value
    assert "1 head" in hover.contents.value
