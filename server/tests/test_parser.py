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
