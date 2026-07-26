from comments import extract_preceding_comment, has_preceding_comment


def test_extract_preceding_single_line_comment():
    text = "% birds are animals\nbird(tweety)."
    pc = extract_preceding_comment(text, statement_line=2)
    assert pc is not None
    assert pc.text == "birds are animals"
    assert pc.start_line == 1
    assert pc.end_line == 1


def test_extract_preceding_multiline_comment():
    text = "% line one\n% line two\nbird(tweety)."
    pc = extract_preceding_comment(text, statement_line=3)
    assert pc is not None
    assert "line one" in pc.text
    assert "line two" in pc.text
    assert pc.start_line == 1
    assert pc.end_line == 2


def test_extract_preceding_allows_blank_between_comment_and_statement():
    text = "% documented\n\nbird(tweety)."
    pc = extract_preceding_comment(text, statement_line=3)
    assert pc is not None
    assert pc.text == "documented"


def test_no_preceding_comment():
    text = "bird(tweety).\nflies(X) :- bird(X)."
    assert extract_preceding_comment(text, statement_line=2) is None
    assert not has_preceding_comment(text, 2)


def test_percent_star_block_counts_as_preceding():
    text = "%*\n#bird(X).\nA bird.\n*%\nbird(tweety)."
    pc = extract_preceding_comment(text, statement_line=5)
    assert pc is not None
    assert has_preceding_comment(text, 5)
