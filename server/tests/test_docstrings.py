from docstrings import (
    extract_docstrings,
    find_param_at_column,
    format_docstring_markdown,
)


SAMPLE = """
%*
#example_predicate(A,B,C).

This is an example predicate used for the illustration of doc strings.

#parameters
    - A : The first argument/parameter of the predicate.
    - B : Another parameter of this example predicate.
    - C : The last parameter in this example.
*%

example_predicate(1, 2, 3).
"""


def test_extract_asp_lsp_style_docstring():
    docs = extract_docstrings(SAMPLE)
    assert ("example_predicate", 3) in docs
    doc = docs[("example_predicate", 3)]
    assert doc.signature == "example_predicate(A, B, C)."
    assert "illustration" in doc.description
    assert len(doc.parameters) == 3
    assert doc.parameters[0].name == "A"
    assert "first argument" in doc.parameters[0].description


def test_format_docstring_markdown():
    doc = extract_docstrings(SAMPLE)[("example_predicate", 3)]
    md = format_docstring_markdown(doc)
    assert "`example_predicate(A, B, C).`" in md
    assert "**Parameters**" in md
    assert "`A`" in md


def test_nullary_signature():
    text = "%*\n#ok.\n\nAlways true.\n*%\nok."
    docs = extract_docstrings(text)
    assert ("ok", 0) in docs
    assert docs[("ok", 0)].signature == "ok."


def test_find_param_at_column():
    # example_predicate(1, 2, 3).
    # 1...............18 19 20 21 22 23 24 25 26
    line = "example_predicate(1, 2, 3)."
    assert find_param_at_column(line, 1, 19, 3) == 0  # on '1'
    assert find_param_at_column(line, 1, 22, 3) == 1  # on '2'
    assert find_param_at_column(line, 1, 25, 3) == 2  # on '3'
    assert find_param_at_column(line, 1, 5, 3) is None  # on name
