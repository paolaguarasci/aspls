from pathlib import Path
from parser import parse_document

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_facts_and_rules_without_errors():
    text = (FIXTURES / "facts_and_rules.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_reports_syntax_error_with_position():
    text = "bird(tweety)\npenguin(pingu)."  # missing dot after first fact
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.errors[0].line == 2


def test_parses_disjunction_aggregates_and_directives():
    text = (FIXTURES / "disjunction_aggregates_directives.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_recovers_after_one_bad_statement_and_parses_the_rest():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.tree is not None
    assert len(result.tree.children) == 2  # bird(tweety). and penguin(pingu).


def test_error_line_number_matches_original_document():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    result = parse_document(text)
    assert result.errors[0].line == 2


def test_multiline_bad_statement_produces_one_error():
    text = "bird(tweety).\nbad statement\nspanning lines\npenguin(pingu)."
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.errors[0].line == 2
    assert result.tree is not None
    assert len(result.tree.children) == 2


def test_large_unparseable_fragment_does_not_crash():
    text = "\n".join(f"not a valid line {i}" for i in range(2000))
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.errors[0].line == 1
    assert result.tree is None
