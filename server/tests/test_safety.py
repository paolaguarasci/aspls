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


def test_equality_to_ground_term_binds_variable():
    """Clingo: X = 0 is an assignment that makes X safe."""
    text = "eq(X) :- X = 0."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_inequality_does_not_bind_variable():
    text = "neq(X) :- X != 0."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert findings[0].variables == ["X"]


def test_comparison_ops_do_not_bind():
    for text in (
        "lt(X) :- X < 10.",
        "le(X) :- X <= 10.",
        "gt(X) :- X > 0.",
        "ge(X) :- X >= 0.",
    ):
        findings = find_unsafe_variables(parse_document(text).tree)
        assert len(findings) == 1, text
        assert findings[0].variables == ["X"], text


def test_interval_assignment_binds_when_bounds_safe():
    text = "cell(X) :- size(N), X = 1..N."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_interval_assignment_from_ground_range():
    text = "cell(Y) :- Y = 1..10."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_chained_equality_assignments_bind():
    """Fixed-point: Y = 1 then X = Y."""
    text = "p(X) :- X = Y, Y = 1."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_equality_between_unbound_vars_is_unsafe():
    text = "same(X, Y) :- X = Y."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert set(findings[0].variables) == {"X", "Y"}


def test_constraint_equality_to_ground_is_safe():
    text = ":- X = 1."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_aggregate_assignment_binds_result_and_local_vars():
    text = "num(N) :- N = #count{ X : node(X) }."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_aggregate_condition_binds_local_vars_in_comparison():
    text = "has_any :- #count{ X : node(X) } > 0."
    assert find_unsafe_variables(parse_document(text).tree) == []


def test_aggregate_body_only_element_does_not_bind_tuple_vars():
    """Clingo parses #count{ node(X) } as terms with empty condition → X unsafe."""
    text = "has_any :- #count{ node(X) } > 0."
    findings = find_unsafe_variables(parse_document(text).tree)
    assert len(findings) == 1
    assert "X" in findings[0].variables


def test_weak_constraint_bound_vars_are_safe():
    for text in (
        ":~ selected(X), expensive(X). [1@1, X]",
        ":~ selected(X). [2@2]",
        ":~ selected(a). [1]",
    ):
        assert find_unsafe_variables(parse_document(text).tree) == [], text


def test_weak_weight_unbound_var_is_unsafe():
    findings = find_unsafe_variables(parse_document(":~ q. [X]").tree)
    assert len(findings) == 1
    assert findings[0].variables == ["X"]


def test_weak_negated_only_var_is_unsafe():
    findings = find_unsafe_variables(parse_document(":~ not p(X). [1, X]").tree)
    assert len(findings) == 1
    assert findings[0].variables == ["X"]
