from features.document_symbols import build_document_symbols


def test_document_symbols_lists_name_arity():
    text = "bird(tweety).\nflies(X) :- bird(X)."
    symbols = build_document_symbols(text)
    names = sorted(s.name for s in symbols)
    assert names == ["bird/1", "flies/1"]


def test_document_symbol_selection_prefers_definition():
    text = "bird(tweety).\nflies(X) :- bird(X)."
    symbols = {s.name: s for s in build_document_symbols(text)}
    bird = symbols["bird/1"]
    # definition is the fact on line 0
    assert bird.selection_range.start.line == 0
    assert "fact" in (bird.detail or "")


def test_document_symbols_empty_program():
    assert build_document_symbols("") == []
    assert build_document_symbols("% just a comment\n") == []


def test_document_symbols_sorted_by_name():
    text = "zebra(1).\napple(1)."
    names = [s.name for s in build_document_symbols(text)]
    assert names == ["apple/1", "zebra/1"]
