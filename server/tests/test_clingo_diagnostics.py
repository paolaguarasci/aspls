from clingo_check import check_with_clingo
from features.diagnostics import build_diagnostics
from parser import parse_document


def test_returns_empty_list_for_safe_program():
    text = "bird(tweety)."
    result = check_with_clingo(text)
    assert result == []


def test_reports_clingo_syntax_errors_with_line():
    # Comma between aggregate elements is invalid Clingo (needs ';').
    text = "ok :- C = #count{ X : p(X), Y : q(Y) }."
    result = check_with_clingo(text)
    assert any(d.severity == "error" for d in result)
    assert any("unexpected" in d.message.lower() for d in result)


def test_lark_rejects_comma_separated_aggregate_elements():
    text = "ok :- C = #count{ X : p(X), Y : q(Y) }."
    result = parse_document(text)
    assert result.errors
    msg = result.errors[0].message
    assert "unexpected ':'" in msg
    assert ";" in msg
    assert "Nessun" not in msg
    assert "Previsto" not in msg


def test_parse_errors_are_english_only():
    text = "exact :- #count{ X : a(X) } = #count{ X : b(X) }."
    result = parse_document(text)
    assert result.errors
    msg = result.errors[0].message
    assert msg.startswith("Syntax error:")
    assert "No terminal matches" not in msg
    assert "Nessun" not in msg


def test_lark_accepts_semicolon_aggregate_elements():
    text = "ok :- C = #count{ X : p(X); Y : q(Y) }."
    result = parse_document(text)
    assert result.errors == []


def test_diagnostics_include_lark_errors_for_invalid_aggregates():
    text = "exact :- #count{ X : a(X) } = #count{ X : b(X) }."
    diagnostics = build_diagnostics(text)
    assert diagnostics
    assert any(d.source == "aspls" and d.severity == 1 for d in diagnostics)


def test_diagnostics_surface_clingo_grounding_errors():
    # Syntax is valid for Lark; Clingo rejects unsafe variables.
    text = "has_any :- #count{ node(X) } > 0."
    diagnostics = build_diagnostics(text)
    assert any(d.source == "aspls (clingo)" for d in diagnostics)
