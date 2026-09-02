from __future__ import annotations

from lsprotocol.types import CodeLens, Command

from features.predicate_tree import _name_range
from symbols import DEFINING_ROLES


def build_code_lenses_from_index(
    uri: str,
    merged_index: dict,
) -> list[CodeLens]:
    lenses: list[CodeLens] = []
    for (name, arity), occurrences in merged_index.items():
        count = len(occurrences)
        for occ in occurrences:
            if occ.uri != uri or occ.role not in DEFINING_ROLES:
                continue
            rng = _name_range(occ.line, occ.column, occ.name)
            lenses.append(
                CodeLens(
                    range=rng,
                    command=Command(
                        title="Run this file",
                        command="aspls.codeLens.runFile",
                        arguments=[uri],
                    ),
                )
            )
            label = "1 occurrence" if count == 1 else f"{count} occurrences"
            lenses.append(
                CodeLens(
                    range=rng,
                    command=Command(
                        title=label,
                        command="aspls.codeLens.showReferences",
                        arguments=[uri, occ.line - 1, occ.column - 1],
                    ),
                )
            )
    lenses.sort(key=lambda lens: (lens.range.start.line, lens.range.start.character))
    return lenses
