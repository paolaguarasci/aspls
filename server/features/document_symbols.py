from __future__ import annotations

from lsprotocol.types import DocumentSymbol, Position, Range, SymbolKind

from parser import parse_document
from symbols import DEFINING_ROLES, build_symbol_index


def build_document_symbols(text: str) -> list[DocumentSymbol]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    symbols: list[DocumentSymbol] = []
    for (name, arity), occurrences in sorted(index.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        roles = sorted({occ.role for occ in occurrences})
        pick = next((o for o in occurrences if o.role in DEFINING_ROLES), occurrences[0])
        start = Position(line=pick.line - 1, character=pick.column - 1)
        end = Position(line=pick.line - 1, character=pick.column - 1 + len(pick.name))
        rng = Range(start=start, end=end)
        detail = f"{', '.join(roles)} · {len(occurrences)} occ"
        symbols.append(
            DocumentSymbol(
                name=f"{name}/{arity}",
                kind=SymbolKind.Function,
                range=rng,
                selection_range=rng,
                detail=detail,
                children=[],
            )
        )
    return symbols
