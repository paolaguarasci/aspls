from dataclasses import dataclass, field
from pathlib import Path

import lark
from lark import Lark, UnexpectedInput

GRAMMAR_PATH = Path(__file__).parent / "grammar" / "asp_core2.lark"

_parser = Lark(GRAMMAR_PATH.read_text(), parser="earley", propagate_positions=True)


@dataclass
class ParseError:
    line: int
    column: int
    message: str


@dataclass
class ParseResult:
    tree: lark.Tree | None
    errors: list[ParseError] = field(default_factory=list)


def _split_top_level_statements(text: str) -> list[tuple[str, int]]:
    statements = []
    line_offset = 0
    current = []
    current_start_line = 0
    for line in text.split("\n"):
        if not current:
            current_start_line = line_offset
        current.append(line)
        if "." in line:
            statements.append(("\n".join(current), current_start_line))
            current = []
        line_offset += 1
    if current and "".join(current).strip():
        statements.append(("\n".join(current), current_start_line))
    return statements


def _offset_tree_lines(tree: lark.Tree, offset: int) -> None:
    # propagate_positions numbers each fragment from line 1; shift back to
    # document-relative lines so symbols.py's occurrence index is correct.
    # Columns are untouched: the split only drops whole leading lines, never
    # partial-line text, so column 1 of a fragment is always column 1 of the
    # corresponding original document line.
    if not tree.meta.empty:
        tree.meta.line += offset
        tree.meta.end_line += offset
    for child in tree.children:
        if isinstance(child, lark.Tree):
            _offset_tree_lines(child, offset)
        elif isinstance(child, lark.Token):
            # Tokens carry their own line/end_line (used e.g. by #show).
            if getattr(child, "line", None) is not None:
                child.line += offset
            if getattr(child, "end_line", None) is not None:
                child.end_line += offset


def _parse_fragment(stmt_text: str, start_line: int) -> tuple[list[lark.Tree], list[ParseError]]:
    # The line-based split joins consecutive dot-less lines with the next
    # line that has a '.', so a single bad statement (no '.' of its own) can
    # end up glued to a valid statement that follows it on a later line.
    # Retry on shrinking suffixes (dropping one leading line at a time) so
    # the valid tail is still recovered instead of being swallowed whole.
    # Iterative rather than recursive: a fragment can consist of thousands of
    # dot-less lines, and recursing once per dropped line would blow the
    # Python call stack instead of returning a structured error.
    first_error: ParseError | None = None
    lines = stmt_text.split("\n")
    line_offset = start_line
    while lines:
        remainder = "\n".join(lines)
        try:
            stmt_tree = _parser.parse(remainder)
            _offset_tree_lines(stmt_tree, line_offset)
            errors = [first_error] if first_error else []
            return list(stmt_tree.children), errors
        except UnexpectedInput as e:
            if first_error is None:
                first_error = ParseError(line=e.line + line_offset, column=e.column, message=str(e))
            lines = lines[1:]
            line_offset += 1
    return [], [first_error]


def parse_document(text: str) -> ParseResult:
    children: list[lark.Tree] = []
    errors: list[ParseError] = []

    for stmt_text, start_line in _split_top_level_statements(text):
        if not stmt_text.strip():
            continue
        stmt_children, stmt_errors = _parse_fragment(stmt_text, start_line)
        children.extend(stmt_children)
        errors.extend(stmt_errors)

    tree = lark.Tree("start", children) if children else None
    return ParseResult(tree=tree, errors=errors)
