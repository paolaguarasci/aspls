from lsprotocol.types import Range, Position

from features.inlay_hints import build_inlay_hints


def _labels(text: str, *, start_line: int = 0, end_line: int | None = None) -> list[tuple[int, int, str]]:
    end_line = end_line if end_line is not None else len(text.split("\n")) - 1
    rng = Range(
        start=Position(line=start_line, character=0),
        end=Position(line=end_line, character=999),
    )
    hints = build_inlay_hints(text, rng)
    return [(h.position.line, h.position.character, h.label) for h in hints]


def test_implicit_nullary_shows_slash_zero():
    text = "bird.\nflies(X) :- bird."
    labels = _labels(text)
    assert (0, 4, "/0") in labels
    assert (1, 16, "/0") in labels


def test_explicit_empty_parens_no_arity_hint():
    text = "bird()."
    labels = _labels(text)
    assert not any(label == "/0" for _, _, label in labels)


def test_compound_atom_no_implicit_arity_hint():
    text = "bird(tweety)."
    labels = _labels(text)
    assert not any(label == "/0" for _, _, label in labels)


def test_unused_singleton_variable_in_body():
    text = "ok :- bird(X), cat(Y)."
    labels = _labels(text)
    assert (0, 12, "unused") in labels
    assert (0, 20, "unused") in labels


def test_variable_used_twice_no_unused_hint():
    text = "flies(X) :- bird(X)."
    labels = _labels(text)
    assert not any(label == "unused" for _, _, label in labels)


def test_underscore_prefixed_variable_no_unused_hint():
    text = "ok :- bird(_X)."
    labels = _labels(text)
    assert not any(label == "unused" for _, _, label in labels)


def test_unused_variable_in_rule_head():
    text = "result(X, Y) :- input(X)."
    labels = _labels(text)
    assert (0, 11, "unused") in labels


def test_inlay_hints_respect_requested_range():
    text = "bird.\nflies(X) :- bird."
    rng = Range(
        start=Position(line=0, character=0),
        end=Position(line=0, character=999),
    )
    hints = build_inlay_hints(text, rng)
    assert all(h.position.line == 0 for h in hints)
    assert any(h.label == "/0" for h in hints)
