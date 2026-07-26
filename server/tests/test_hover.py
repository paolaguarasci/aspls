from features.hover import build_hover


def test_hover_over_predicate_shows_name_arity_and_counts():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    hover = build_hover(text, line=1, column=13)
    assert hover is not None
    assert "bird/1" in hover.contents.value
    assert "1 head" in hover.contents.value
    assert "1 body" in hover.contents.value


def test_hover_over_whitespace_returns_none():
    text = "bird(tweety)."
    hover = build_hover(text, line=0, column=0)  # position of 'b', still on atom
    assert hover is not None
    # move to a position clearly past the statement (blank) to assert None
    hover_none = build_hover(text, line=5, column=0)
    assert hover_none is None
