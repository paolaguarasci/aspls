from lsprotocol.types import SemanticTokens

from parser import parse_document
from symbols import collect_occurrences

# Order is the legend index used by the client.
TOKEN_TYPES = [
    "aspFact",
    "aspRuleHead",
    "aspRuleBody",
    "aspConstraint",
    "aspShow",
    "aspMinimize",
]

TOKEN_MODIFIERS = [
    "aspNegated",
]

_ROLE_TO_TYPE = {
    "fact": "aspFact",
    "rule_head": "aspRuleHead",
    "rule_body": "aspRuleBody",
    "constraint": "aspConstraint",
    "show": "aspShow",
    "minimize": "aspMinimize",
    "weak": "aspMinimize",
}


def build_semantic_tokens(text: str) -> SemanticTokens:
    result = parse_document(text)
    occurrences = collect_occurrences(result.tree)
    occurrences.sort(key=lambda o: (o.line, o.column))

    data: list[int] = []
    prev_line = 0
    prev_col = 0
    for occ in occurrences:
        token_type = _ROLE_TO_TYPE.get(occ.role)
        if token_type is None:
            continue
        type_idx = TOKEN_TYPES.index(token_type)
        modifiers = 1 << TOKEN_MODIFIERS.index("aspNegated") if occ.negated else 0

        # Lark positions are 1-based; LSP semantic tokens are 0-based deltas.
        line = occ.line - 1
        col = occ.column - 1
        delta_line = line - prev_line
        delta_col = col - prev_col if delta_line == 0 else col
        data.extend([delta_line, delta_col, len(occ.name), type_idx, modifiers])
        prev_line = line
        prev_col = col

    return SemanticTokens(data=data)
