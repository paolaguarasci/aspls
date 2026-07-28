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


def test_document_symbols_nested_role_groups():
    text = "bird(tweety).\nflies(X) :- bird(X), not bird(X)."
    symbols = {s.name: s for s in build_document_symbols(text)}
    bird = symbols["bird/1"]
    assert bird.children is not None
    role_names = [c.name for c in bird.children]
    assert role_names == ["fact", "rule_body"]
    fact = bird.children[0]
    assert fact.detail == "1 occ"
    assert len(fact.children) == 1
    assert fact.children[0].name == "L1:1"
    body = bird.children[1]
    assert body.detail == "2 occ"
    labels = [c.name for c in body.children]
    assert labels == ["L2:13", "not L2:26"]


def test_document_symbols_role_order_fixed():
    text = "p(1).\n:- p(1).\np(X) :- q(X)."
    # p has fact, rule_head, constraint — order must not be alpha
    p = next(s for s in build_document_symbols(text) if s.name == "p/1")
    assert [c.name for c in p.children] == ["fact", "rule_head", "constraint"]


def test_document_symbols_weak_role_after_minimize():
    text = (
        "cost(a).\n"
        "#minimize { 1, X : cost(X) }.\n"
        ":~ cost(X). [1@1, X]\n"
    )
    cost = next(s for s in build_document_symbols(text) if s.name == "cost/1")
    assert [c.name for c in cost.children] == ["fact", "minimize", "weak"]
