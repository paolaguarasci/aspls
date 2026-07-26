from parser import parse_document
from symbols import build_symbol_index


def test_indexes_head_and_body_occurrences():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    assert ("bird", 1) in index
    bird_occurrences = index[("bird", 1)]
    assert len(bird_occurrences) == 2
    roles = {occ.role for occ in bird_occurrences}
    assert roles == {"head", "body"}

    assert ("flies", 1) in index
    assert index[("flies", 1)][0].role == "head"

    assert ("penguin", 1) in index
    assert index[("penguin", 1)][0].role == "body"


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
