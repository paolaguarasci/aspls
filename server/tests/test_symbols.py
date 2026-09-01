from parser import parse_document
from symbols import USING_ROLES, build_symbol_index, find_key_at


def test_indexes_head_and_body_occurrences():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert ("bird", 1) in index
    bird_occurrences = index[("bird", 1)]
    assert len(bird_occurrences) == 2
    roles = {occ.role for occ in bird_occurrences}
    assert roles == {"fact", "rule_body"}

    assert ("flies", 1) in index
    assert index[("flies", 1)][0].role == "rule_head"

    assert ("penguin", 1) in index
    assert index[("penguin", 1)][0].role == "rule_body"
    assert index[("penguin", 1)][0].negated is True


def test_nullary_atom_has_arity_zero():
    text = "sunny."
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    assert ("sunny", 0) in index


def test_occurrences_report_document_relative_line_for_every_statement():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    bird_lines = {occ.line for occ in index[("bird", 1)]}
    assert bird_lines == {1, 2}  # fact on line 1, body occurrence on line 2

    assert index[("flies", 1)][0].line == 2
    assert index[("penguin", 1)][0].line == 2


def test_occurrence_line_correct_after_error_recovery_drops_lines():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert index[("bird", 1)][0].line == 1
    assert index[("penguin", 1)][0].line == 3  # not 1, the dropped fragment's line


def test_find_key_at_matches_occurrence_position():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert find_key_at(index, 1, 1) == ("bird", 1)
    assert find_key_at(index, 2, 13) == ("bird", 1)
    assert find_key_at(index, 1, 5) is None


def test_indexes_constraint_show_and_minimize():
    text = ":- bird(X).\n#show bird/1.\n#minimize { 1, X : cost(X) }."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert index[("bird", 1)][0].role == "constraint"
    assert any(o.role == "show" for o in index[("bird", 1)])
    assert index[("cost", 1)][0].role == "minimize"


def test_indexes_weak_constraint_body_atoms():
    text = "selected(a).\n:~ selected(X). [1@1, X]"
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert ("selected", 1) in index
    roles = {o.role for o in index[("selected", 1)]}
    assert "weak" in roles
    weak_occs = [o for o in index[("selected", 1)] if o.role == "weak"]
    assert len(weak_occs) == 1
    assert weak_occs[0].line == 2


def test_weak_role_is_a_using_role():
    assert "weak" in USING_ROLES


def test_indexes_external_directive_atoms():
    text = "#external query(T) : step(T).\nstep(1)."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert ("query", 1) in index
    assert index[("query", 1)][0].role == "external"
    assert ("step", 1) in index
    roles = {o.role for o in index[("step", 1)]}
    assert "external" in roles
    assert "fact" in roles


def test_external_role_is_a_using_role():
    assert "external" in USING_ROLES


def test_weak_weight_terms_are_not_indexed_as_atoms():
    """Weight bracket has only terms (e.g. X) — no atom occurrences from weight."""
    text = ":~ q. [X]"
    index = build_symbol_index(parse_document(text).tree)
    # q/0 from body; no spurious keys from weight var X
    assert ("q", 0) in index
    assert index[("q", 0)][0].role == "weak"
    assert all(key[0] != "X" for key in index)
