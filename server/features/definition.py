from lsprotocol.types import Location, Position, Range

from parser import parse_document
from symbols import Occurrence, build_symbol_index


def _find_key_at(
    index: dict[tuple[str, int], list[Occurrence]], line_1indexed: int, column_1indexed: int
) -> tuple[str, int] | None:
    for (name, arity), occurrences in index.items():
        for occ in occurrences:
            token_end_column = occ.column + len(occ.name)
            if occ.line == line_1indexed and occ.column <= column_1indexed < token_end_column:
                return (name, arity)
    return None


def build_definitions(text: str, line: int, column: int, uri: str) -> list[Location]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    key = _find_key_at(index, line + 1, column + 1)
    if key is None:
        return []

    locations = []
    for occ in index[key]:
        if occ.role != "head":
            continue
        start = Position(line=occ.line - 1, character=occ.column - 1)
        end = Position(line=occ.line - 1, character=occ.column - 1 + len(occ.name))
        locations.append(Location(uri=uri, range=Range(start=start, end=end)))
    return locations
