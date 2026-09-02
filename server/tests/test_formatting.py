from constructs import collect_constructs, find_order_violations
from features.formatting import build_format_edits


def test_format_edits_reorders_out_of_order_document():
    text = "#show bird/1.\n% a bird\nbird(tweety).\n"
    edits = build_format_edits(text)
    assert edits is not None
    assert len(edits) == 1
    new_text = edits[0].new_text
    assert find_order_violations(collect_constructs(new_text)) == []
    assert new_text.index("bird(tweety)") < new_text.index("#show")


def test_format_edits_noop_when_already_sorted():
    text = "% a bird\nbird(tweety).\n% show\n#show bird/1.\n"
    assert build_format_edits(text) is None


def test_format_edits_full_document_range():
    text = "#show bird/1.\nbird(tweety)."
    edits = build_format_edits(text)
    assert edits is not None
    edit = edits[0]
    assert edit.range.start.line == 0
    assert edit.range.start.character == 0
    assert edit.range.end.line == 1
    assert edit.range.end.character == len("bird(tweety).")
