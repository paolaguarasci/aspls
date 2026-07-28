from __future__ import annotations

from lsprotocol.types import DocumentSymbol, Position, Range, SymbolKind

from symbols import DEFINING_ROLES, Occurrence

ROLE_ORDER = ("fact", "rule_head", "rule_body", "constraint", "show", "minimize", "weak")


def _name_range(line: int, column: int, name: str) -> Range:
    start = Position(line=line - 1, character=column - 1)
    end = Position(line=line - 1, character=column - 1 + len(name))
    return Range(start=start, end=end)


def _occ_label(line: int, column: int, *, negated: bool = False) -> str:
    base = f"L{line}:{column}"
    return f"not {base}" if negated else base


def build_document_symbols_from_index(
    index: dict[tuple[str, int], list[Occurrence]],
) -> list[DocumentSymbol]:
    symbols: list[DocumentSymbol] = []
    for (name, arity), occurrences in sorted(index.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        roles_present = {o.role for o in occurrences}
        pick = next((o for o in occurrences if o.role in DEFINING_ROLES), occurrences[0])
        parent_rng = _name_range(pick.line, pick.column, pick.name)
        detail = f"{', '.join(sorted(roles_present))} · {len(occurrences)} occ"
        role_children: list[DocumentSymbol] = []
        for role in ROLE_ORDER:
            group = [o for o in occurrences if o.role == role]
            if not group:
                continue
            first = group[0]
            grp_rng = _name_range(first.line, first.column, first.name)
            occ_children = [
                DocumentSymbol(
                    name=_occ_label(o.line, o.column, negated=o.negated),
                    kind=SymbolKind.Variable,
                    range=_name_range(o.line, o.column, o.name),
                    selection_range=_name_range(o.line, o.column, o.name),
                    children=[],
                )
                for o in group
            ]
            role_children.append(
                DocumentSymbol(
                    name=role,
                    kind=SymbolKind.Namespace,
                    range=grp_rng,
                    selection_range=grp_rng,
                    detail=f"{len(group)} occ",
                    children=occ_children,
                )
            )
        symbols.append(
            DocumentSymbol(
                name=f"{name}/{arity}",
                kind=SymbolKind.Function,
                range=parent_rng,
                selection_range=parent_rng,
                detail=detail,
                children=role_children,
            )
        )
    return symbols
