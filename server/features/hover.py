from lsprotocol.types import Hover, MarkupContent, MarkupKind

from parser import parse_document
from symbols import DEFINING_ROLES, USING_ROLES, build_symbol_index, find_key_at


def build_hover_from_index(
    index: dict,
    line: int,
    column: int,
    uri: str | None = None,
    *,
    document_index: dict | None = None,
) -> Hover | None:
    """Resolve cursor key from the active document, then count in ``index``."""
    resolve_index = document_index if document_index is not None else index
    resolve_uri = None if document_index is not None else uri
    key = find_key_at(resolve_index, line + 1, column + 1, resolve_uri)
    if key is None:
        return None

    name, arity = key
    occurrences = index.get(key, [])
    head_count = sum(1 for occ in occurrences if occ.role in DEFINING_ROLES)
    body_count = sum(1 for occ in occurrences if occ.role in USING_ROLES)

    text_value = f"**{name}/{arity}**\n\n{head_count} head occurrence(s), {body_count} body occurrence(s)"
    return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=text_value))


def build_hover(text: str, line: int, column: int) -> Hover | None:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    return build_hover_from_index(index, line, column, document_index=index)
