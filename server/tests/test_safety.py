from parser import parse_document
from safety import find_unsafe_variables


def test_safe_rule_has_no_findings():
    text = "flies(X) :- bird(X)."
    tree = parse_document(text).tree
    assert find_unsafe_variables(tree) == []


def test_head_variable_without_body_binder_is_unsafe():
    text = "flies(X) :- bird(Y)."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert findings[0].variables == ["X"]


def test_variable_only_under_negation_is_unsafe():
    text = "ok :- not bird(X)."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert "X" in findings[0].variables


def test_constraint_with_unbound_var_is_unsafe():
    text = ":- p(X)."
    # X appears in positive body atom → safe for constraints that bind in positive atom.
    # Use comparison-only to force unsafe:
    text = ":- X = Y."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert set(findings[0].variables) == {"X", "Y"}


def test_fact_with_variable_is_unsafe():
    text = "bird(X)."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert findings[0].variables == ["X"]


def test_range_bound_variable_in_positive_atom_is_safe():
    """Bare VARIABLE in range_bound must be collected (not only var_term).

    Regression: q(X) :- p(1..X). falsely reported unsafe X when
    _collect_vars skipped Token VARIABLE under range_bound.
    """
    text = "q(X) :- p(1..X)."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert findings == []
