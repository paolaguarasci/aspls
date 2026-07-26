from lsprotocol.types import Location, Position, Range

from parser import parse_document
from symbols import build_symbol_index, find_key_at


def build_references(text: str, line: int, column: int, uri: str) -> list[Location]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    key = find_key_at(index, line + 1, column + 1)
    if key is None:
        return []

    locations = []
    for occ in index[key]:
        start = Position(line=occ.line - 1, character=occ.column - 1)
        end = Position(line=occ.line - 1, character=occ.column - 1 + len(occ.name))
        locations.append(Location(uri=uri, range=Range(start=start, end=end)))
    return locations
