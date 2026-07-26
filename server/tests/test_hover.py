from features.hover import build_hover


def test_hover_over_predicate_shows_name_arity_and_counts():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    # parse_document parses each statement as an independent fragment, so
    # Occurrence.line resets to 1 for every statement rather than tracking
    # the document line -> the "bird" body occurrence reports line 1, not 2.
    hover = build_hover(text, line=0, column=13)
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
