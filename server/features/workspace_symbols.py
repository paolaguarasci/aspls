from __future__ import annotations

from lsprotocol.types import Location, Position, Range, SymbolInformation, SymbolKind

from symbols import DEFINING_ROLES
from workspace_index import IndexedOccurrence


def _name_range(line: int, column: int, name: str) -> Range:
    start = Position(line=line - 1, character=column - 1)
    end = Position(line=line - 1, character=column - 1 + len(name))
    return Range(start=start, end=end)


def _matches_query(name: str, arity: int, query: str) -> bool:
    if not query:
        return True
    label = f"{name}/{arity}"
    q = query.casefold()
    return q in name.casefold() or q in label.casefold()


def build_workspace_symbols(
    merged: dict[tuple[str, int], list[IndexedOccurrence]],
    query: str,
) -> list[SymbolInformation]:
    symbols: list[SymbolInformation] = []
    for (name, arity), occurrences in sorted(merged.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if not _matches_query(name, arity, query):
            continue
        pick = next((o for o in occurrences if o.role in DEFINING_ROLES), occurrences[0])
        symbols.append(
            SymbolInformation(
                name=f"{name}/{arity}",
                kind=SymbolKind.Function,
                location=Location(
                    uri=pick.uri,
                    range=_name_range(pick.line, pick.column, pick.name),
                ),
            )
        )
    return symbols
