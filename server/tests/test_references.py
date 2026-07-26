from features.references import build_references


def test_references_returns_all_occurrences_head_and_body():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    locations = build_references(text, line=0, column=1, uri="file:///test.lp")  # cursor on "bird" in fact
    assert len(locations) == 2  # fact head + rule body
    lines = sorted(loc.range.start.line for loc in locations)
    assert lines == [0, 1]


def test_references_over_non_predicate_returns_empty():
    text = "bird(tweety)."
    locations = build_references(text, line=10, column=0, uri="file:///test.lp")
    assert locations == []
