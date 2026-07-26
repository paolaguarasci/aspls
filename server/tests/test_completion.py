from lsprotocol.types import InsertTextFormat

from features.completion import build_completions


def test_completions_list_all_known_predicates():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    items = build_completions(text)
    labels = {item.label for item in items}
    assert labels == {"bird/1", "flies/1", "penguin/1"}


def test_completion_snippet_for_nonzero_arity():
    text = "bird(tweety)."
    items = build_completions(text)
    item = next(i for i in items if i.label == "bird/1")
    assert item.insert_text == "bird(${1:X1})"
    assert item.insert_text_format == InsertTextFormat.Snippet


def test_completion_snippet_for_arity_two():
    text = "edge(a, b)."
    items = build_completions(text)
    item = next(i for i in items if i.label == "edge/2")
    assert item.insert_text == "edge(${1:X1}, ${2:X2})"
    assert item.insert_text_format == InsertTextFormat.Snippet


def test_completion_insert_text_has_no_paren_for_nullary():
    text = "sunny."
    items = build_completions(text)
    item = items[0]
    assert item.insert_text == "sunny"
    assert item.insert_text_format in (None, InsertTextFormat.PlainText)
