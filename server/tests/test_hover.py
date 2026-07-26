from features.hover import build_hover


def test_hover_over_predicate_shows_name_arity_and_counts():
    text = "bird(tweety).\nflies(X) :- bird(X), not penguin(X)."
    hover = build_hover(text, line=1, column=13)
    assert hover is not None
    assert "bird/1" in hover.contents.value
    assert "1 head" in hover.contents.value
    assert "1 body" in hover.contents.value


def test_hover_over_whitespace_returns_none():
    text = "bird(tweety)."
    hover = build_hover(text, line=0, column=0)  # position of 'b', still on atom
    assert hover is not None
    # move to a position clearly past the statement (blank) to assert None
    hover_none = build_hover(text, line=5, column=0)
    assert hover_none is None


def test_hover_shows_docstring():
    text = (
        "%*\n"
        "#bird(X).\n"
        "\n"
        "A flying animal.\n"
        "\n"
        "#parameters\n"
        "    - X : The individual.\n"
        "*%\n"
        "bird(tweety).\n"
    )
    hover = build_hover(text, line=8, column=0)
    assert hover is not None
    value = hover.contents.value
    assert "bird/1" in value
    assert "flying animal" in value
    assert "Parameters" in value
    assert "The individual" in value


def test_hover_shows_preceding_comment_and_definition():
    text = "% penguins cannot fly\npenguin(pingu).\nflies(X) :- bird(X), not penguin(X)."
    hover = build_hover(text, line=2, column=28)  # penguin in body
    assert hover is not None
    value = hover.contents.value
    assert "penguin/1" in value
    assert "Definition" in value
    assert "penguin(pingu)." in value
    assert "Comment" in value
    assert "penguins cannot fly" in value


def test_hover_param_description():
    text = (
        "%*\n"
        "#edge(A,B).\n"
        "\n"
        "Directed edge.\n"
        "\n"
        "#parameters\n"
        "    - A : Source node.\n"
        "    - B : Target node.\n"
        "*%\n"
        "edge(1, 2).\n"
    )
    # cursor on second argument '2' — column of '2' in "edge(1, 2)."
    # edge(1, 2). → 2 is at column 9 (1-based) → column 8 (0-based)
    hover = build_hover(text, line=9, column=8)
    assert hover is not None
    assert "Target node" in hover.contents.value


def test_hover_definition_stays_on_same_predicate():
    """Do not show another predicate's line as the definition."""
    from features.hover import build_hover_from_index
    from workspace_index import IndexedOccurrence

    # Active file only uses ordinato; merged pool has ordered at the same line
    # number in another URI — classic cross-file line collision.
    active = "ordinato(a, b).\n"
    merged = {
        ("ordinato", 2): [
            IndexedOccurrence(
                name="ordinato",
                arity=2,
                line=1,
                column=1,
                role="fact",
                uri="file:///active.lp",
            )
        ],
        ("ordered", 2): [
            IndexedOccurrence(
                name="ordered",
                arity=2,
                line=1,
                column=1,
                role="rule_head",
                uri="file:///other.lp",
            )
        ],
    }
    doc_index = {
        ("ordinato", 2): merged[("ordinato", 2)],
    }
    hover = build_hover_from_index(
        merged,
        0,
        0,
        "file:///active.lp",
        document_index=doc_index,
        source=active,
    )
    assert hover is not None
    value = hover.contents.value
    assert "ordinato/2" in value
    assert "ordinato(a, b)." in value
    assert "ordered" not in value


def test_hover_ignores_foreign_file_definition_line_numbers():
    """Never map another file's definition line onto the active buffer."""
    from features.hover import build_hover_from_index
    from workspace_index import IndexedOccurrence

    # Active buffer line 1 is ordered(...); ordinato is defined at line 1 in other.lp
    # and only used here in a constraint (body). Old bug: showed ordered as Definition.
    active = (
        "ordered(X, Y) :- candidate(X), candidate(Y), X < Y.\n"
        ":- not ordinato(1, 2).\n"
    )
    merged = {
        ("ordered", 2): [
            IndexedOccurrence(
                name="ordered",
                arity=2,
                line=1,
                column=1,
                role="rule_head",
                uri="file:///active.lp",
            ),
        ],
        ("ordinato", 2): [
            IndexedOccurrence(
                name="ordinato",
                arity=2,
                line=1,
                column=1,
                role="rule_head",
                uri="file:///other.lp",
            ),
            IndexedOccurrence(
                name="ordinato",
                arity=2,
                line=2,
                column=8,
                role="constraint",
                uri="file:///active.lp",
            ),
        ],
        ("candidate", 1): [],
    }
    doc_index = {
        ("ordered", 2): merged[("ordered", 2)],
        ("ordinato", 2): [merged[("ordinato", 2)][1]],
    }
    hover = build_hover_from_index(
        merged,
        1,
        8,
        "file:///active.lp",
        document_index=doc_index,
        source=active,
    )
    assert hover is not None
    value = hover.contents.value
    assert "ordinato/2" in value
    # Must not claim ordered(...) is the definition of ordinato
    assert "ordered(X, Y)" not in value
