from __future__ import annotations

import lark
from lsprotocol.types import InlayHint, InlayHintKind, Position, Range

from parser import parse_document
from safety import _collect_vars
from symbols import collect_occurrences


def _position_in_range(line: int, character: int, rng: Range) -> bool:
    if line < rng.start.line or line > rng.end.line:
        return False
    if line == rng.start.line and character < rng.start.character:
        return False
    if line == rng.end.line and character > rng.end.character:
        return False
    return True


def _is_implicit_nullary(source: str, line: int, column: int, name: str) -> bool:
    """True when a nullary atom is written without parentheses."""
    lines = source.split("\n")
    if line < 1 or line > len(lines):
        return False
    line_text = lines[line - 1]
    start = column - 1
    end = start + len(name)
    if line_text[start:end] != name:
        return False
    rest = line_text[end:].lstrip()
    return not rest.startswith("(")


def _unused_singleton_vars(statement: lark.Tree) -> list[tuple[str, int, int]]:
    found: list[tuple[str, int, int]] = []
    _collect_vars(statement, found)
    counts: dict[str, int] = {}
    for name, _, _ in found:
        counts[name] = counts.get(name, 0) + 1
    unused: list[tuple[str, int, int]] = []
    for name, line, column in found:
        if counts[name] != 1:
            continue
        if name.startswith("_"):
            continue
        unused.append((name, line, column))
    return unused


def _arity_hints(source: str, occurrences, rng: Range) -> list[InlayHint]:
    hints: list[InlayHint] = []
    for occ in occurrences:
        if occ.arity != 0:
            continue
        if not _is_implicit_nullary(source, occ.line, occ.column, occ.name):
            continue
        line = occ.line - 1
        character = occ.column - 1 + len(occ.name)
        if not _position_in_range(line, character, rng):
            continue
        hints.append(
            InlayHint(
                position=Position(line=line, character=character),
                label="/0",
                kind=InlayHintKind.Type,
                padding_left=False,
                padding_right=True,
            )
        )
    return hints


def _unused_var_hints(tree: lark.Tree | None, rng: Range) -> list[InlayHint]:
    if tree is None:
        return []
    hints: list[InlayHint] = []
    for statement_wrapper in tree.children:
        statement = statement_wrapper.children[0]
        for name, line, column in _unused_singleton_vars(statement):
            lsp_line = line - 1
            lsp_col = column - 1 + len(name)
            if not _position_in_range(lsp_line, lsp_col, rng):
                continue
            hints.append(
                InlayHint(
                    position=Position(line=lsp_line, character=lsp_col),
                    label="unused",
                    kind=InlayHintKind.Parameter,
                    padding_left=False,
                    padding_right=True,
                )
            )
    return hints


def build_inlay_hints(text: str, range: Range) -> list[InlayHint]:
    result = parse_document(text)
    occurrences = collect_occurrences(result.tree)
    hints = _arity_hints(text, occurrences, range)
    hints.extend(_unused_var_hints(result.tree, range))
    hints.sort(key=lambda h: (h.position.line, h.position.character))
    return hints
