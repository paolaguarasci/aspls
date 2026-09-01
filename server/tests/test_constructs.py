from constructs import (
    ConstructKind,
    classify_statement,
    collect_constructs,
    find_order_violations,
    reorder_constructs,
)


def test_classify_kinds():
    assert classify_statement("#const n = 3.") == ConstructKind.CONSTANTS
    assert classify_statement("bird(tweety).") == ConstructKind.FACTS
    assert classify_statement("{ bird(X) : animal(X) }.") == ConstructKind.CHOICES
    assert classify_statement("flies(X) :- bird(X).") == ConstructKind.DEFINITIONS
    assert classify_statement(":- penguin(X), flies(X).") == ConstructKind.CONSTRAINTS
    assert classify_statement("#minimize { 1, X : cost(X) }.") == ConstructKind.OPTIMIZATION
    assert classify_statement("#maximize { 1, X : reward(X) }.") == ConstructKind.OPTIMIZATION
    assert classify_statement(":~ cost(X). [1,X]") == ConstructKind.OPTIMIZATION
    assert classify_statement("#show bird/1.") == ConstructKind.SHOW


def test_collect_attaches_preceding_comment():
    text = "% a bird\nbird(tweety).\n#show bird/1."
    constructs = collect_constructs(text)
    assert len(constructs) == 2
    assert constructs[0].kind == ConstructKind.FACTS
    assert constructs[0].has_preceding_comment
    assert constructs[1].kind == ConstructKind.SHOW
    assert not constructs[1].has_preceding_comment


def test_order_violations():
    text = "#show bird/1.\nbird(tweety)."
    constructs = collect_constructs(text)
    violations = find_order_violations(constructs)
    assert len(violations) == 1
    assert violations[0].kind == ConstructKind.FACTS


def test_no_order_violations_when_sorted():
    text = "#const n = 1.\nbird(a).\nflies(X) :- bird(X).\n:- bad(X).\n#show bird/1."
    constructs = collect_constructs(text)
    assert find_order_violations(constructs) == []


def test_reorder_constructs():
    text = "#show bird/1.\n% a bird\nbird(tweety).\n"
    out = reorder_constructs(text)
    constructs = collect_constructs(out)
    assert [c.kind for c in constructs] == [ConstructKind.FACTS, ConstructKind.SHOW]
    assert constructs[0].has_preceding_comment
    assert find_order_violations(constructs) == []
