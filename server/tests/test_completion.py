from features.completion import build_completions


def test_completions_list_all_known_predicates():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    items = build_completions(text)
    labels = {item.label for item in items}
    assert labels == {"bird/1", "flies/1", "penguin/1"}


def test_completion_insert_text_includes_paren_for_nonzero_arity():
    text = "bird(tweety)."
    items = build_completions(text)
    assert items[0].insert_text == "bird("


def test_completion_insert_text_has_no_paren_for_nullary():
    text = "sunny."
    items = build_completions(text)
    assert items[0].insert_text == "sunny"
