from features.semantic_tokens import TOKEN_MODIFIERS, TOKEN_TYPES, build_semantic_tokens


def _decode(data: list[int]) -> list[tuple[int, int, int, str, int]]:
    """Return (line, col, length, type_name, modifiers) absolute positions."""
    line = 0
    col = 0
    out = []
    for i in range(0, len(data), 5):
        delta_line, delta_col, length, type_idx, modifiers = data[i : i + 5]
        if delta_line == 0:
            col += delta_col
        else:
            line += delta_line
            col = delta_col
        out.append((line, col, length, TOKEN_TYPES[type_idx], modifiers))
    return out


def test_semantic_tokens_distinguish_fact_rule_constraint_show():
    text = "\n".join(
        [
            "bird(tweety).",
            "flies(X) :- bird(X), not penguin(X).",
            ":- bird(X).",
            "#show flies/1.",
            "#minimize { 1, X : penalty(X) }.",
        ]
    )
    tokens = build_semantic_tokens(text)
    decoded = _decode(tokens.data)

    by_name = {}
    for line, col, length, typ, mods in decoded:
        name = text.split("\n")[line][col : col + length]
        by_name.setdefault(name, []).append((typ, mods))

    assert ("aspFact", 0) in by_name["bird"]
    assert ("aspRuleBody", 0) in by_name["bird"]
    assert ("aspConstraint", 0) in by_name["bird"]
    assert ("aspRuleHead", 0) in by_name["flies"]
    assert ("aspShow", 0) in by_name["flies"]
    assert ("aspRuleBody", 1 << TOKEN_MODIFIERS.index("aspNegated")) in by_name[
        "penguin"
    ]
    assert ("aspMinimize", 0) in by_name["penalty"]


def test_semantic_tokens_empty_on_empty_document():
    tokens = build_semantic_tokens("")
    assert tokens.data == []


def test_semantic_tokens_weak_maps_to_minimize_type():
    text = ":~ penalty(X). [1, X]"
    data = build_semantic_tokens(text).data
    # One atom token: penalty — type index must be aspMinimize
    minimize_idx = TOKEN_TYPES.index("aspMinimize")
    assert minimize_idx in {data[i] for i in range(3, len(data), 5)}


def test_semantic_tokens_maximize_maps_to_minimize_type():
    text = "#maximize { 1, X : reward(X) }."
    data = build_semantic_tokens(text).data
    minimize_idx = TOKEN_TYPES.index("aspMinimize")
    assert minimize_idx in {data[i] for i in range(3, len(data), 5)}
