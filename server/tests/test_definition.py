from features.definition import build_definitions


def test_definition_returns_all_head_occurrences():
    text = "bird(tweety).\nbird(polly).\nflies(X) :- bird(X)."
    # cursor over "bird" inside the rule body, line index 2, around column 13
    locations = build_definitions(text, line=2, column=13, uri="file:///test.lp")
    assert len(locations) == 2
    lines = sorted(loc.range.start.line for loc in locations)
    assert lines == [0, 1]
    assert all(loc.uri == "file:///test.lp" for loc in locations)


def test_definition_over_non_predicate_returns_empty():
    text = "bird(tweety)."
    locations = build_definitions(text, line=10, column=0, uri="file:///test.lp")
    assert locations == []
