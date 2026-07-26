from lsprotocol.types import Hover, MarkupContent, MarkupKind

from parser import parse_document
from symbols import DEFINING_ROLES, USING_ROLES, build_symbol_index, find_key_at


def build_hover(text: str, line: int, column: int) -> Hover | None:
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    key = find_key_at(index, line + 1, column + 1)
    if key is None:
        return None

    name, arity = key
    occurrences = index[key]
    head_count = sum(1 for occ in occurrences if occ.role in DEFINING_ROLES)
    body_count = sum(1 for occ in occurrences if occ.role in USING_ROLES)

    text_value = f"**{name}/{arity}**\n\n{head_count} head occurrence(s), {body_count} body occurrence(s)"
    return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=text_value))
