from lsprotocol.types import Location, Position, Range

from parser import parse_document
from symbols import DEFINING_ROLES, build_symbol_index, find_key_at


def build_definitions_from_index(
    index: dict,
    line: int,
    column: int,
    uri: str | None = None,
    *,
    document_index: dict | None = None,
) -> list[Location]:
    """Resolve cursor key from the active document, then look up in ``index``.

    ``document_index`` (preferred) or ``uri`` filter avoids matching another
    file's predicate at the same (line, column) in a merged index.
    """
    resolve_index = document_index if document_index is not None else index
    resolve_uri = None if document_index is not None else uri
    key = find_key_at(resolve_index, line + 1, column + 1, resolve_uri)
    if key is None:
        return []

    locations = []
    for occ in index.get(key, []):
        if occ.role not in DEFINING_ROLES:
            continue
        loc_uri = getattr(occ, "uri", None) or uri
        if loc_uri is None:
            continue
        start = Position(line=occ.line - 1, character=occ.column - 1)
        end = Position(line=occ.line - 1, character=occ.column - 1 + len(occ.name))
        locations.append(Location(uri=loc_uri, range=Range(start=start, end=end)))
    return locations


def build_definitions(text: str, line: int, column: int, uri: str) -> list[Location]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    return build_definitions_from_index(index, line, column, uri, document_index=index)
