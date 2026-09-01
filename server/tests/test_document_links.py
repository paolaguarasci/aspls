from pathlib import Path

from features.document_links import build_document_links
from workspace_index import resolve_entry_path

FIXTURES = Path(__file__).parent / "fixtures"
INCLUDE_MAIN = FIXTURES / "include_main.lp"
INCLUDE_FACTS = FIXTURES / "include_facts.lp"


def test_document_link_for_include_in_fixture():
    main_uri = INCLUDE_MAIN.resolve().as_uri()
    facts_uri = INCLUDE_FACTS.resolve().as_uri()
    workspace_root = str(FIXTURES.parent.parent.parent.resolve())
    text = INCLUDE_MAIN.read_text()

    links = build_document_links(text, main_uri, [workspace_root])
    assert len(links) == 1

    link = links[0]
    assert link.target == facts_uri
    assert link.range.start.line == 0
    assert link.range.start.character == 10
    assert link.range.end.line == 0
    assert link.range.end.character == 26


def test_document_link_range_excludes_quotes():
    uri = "file:///proj/main.lp"
    text = '#include "facts.lp".\nbird(a).'

    links = build_document_links(text, uri, ["/proj"])
    assert len(links) == 1
    link = links[0]
    assert link.range.start.character == 10
    assert link.range.end.character == 18


def test_document_link_target_matches_resolve_entry_path():
    uri = "file:///proj/sub/main.lp"
    text = '#include "shared/facts.lp".'

    links = build_document_links(text, uri, ["/proj"])
    expected = resolve_entry_path(uri, "shared/facts.lp", ["/proj"])
    assert links[0].target == expected


def test_no_links_when_no_includes():
    links = build_document_links("bird(a).", "file:///x.lp", ["/"])
    assert links == []
