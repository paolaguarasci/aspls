"""Classify top-level ASP constructs for learner-mode rule ordering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from comments import (
    _is_blank,
    _is_block_close,
    _is_block_open,
    _is_percent_line_comment,
    extract_preceding_comment,
)
from parser import _split_top_level_statements


class ConstructKind(IntEnum):
    CONSTANTS = 0
    FACTS = 1
    CHOICES = 2
    DEFINITIONS = 3
    CONSTRAINTS = 4
    OPTIMIZATION = 5
    SHOW = 6
    UNKNOWN = 99


KIND_LABELS = {
    ConstructKind.CONSTANTS: "constants",
    ConstructKind.FACTS: "facts",
    ConstructKind.CHOICES: "choices",
    ConstructKind.DEFINITIONS: "definitions",
    ConstructKind.CONSTRAINTS: "constraints",
    ConstructKind.OPTIMIZATION: "optimization",
    ConstructKind.SHOW: "show",
    ConstructKind.UNKNOWN: "unknown",
}

EXPECTED_ORDER = (
    ConstructKind.CONSTANTS,
    ConstructKind.FACTS,
    ConstructKind.CHOICES,
    ConstructKind.DEFINITIONS,
    ConstructKind.CONSTRAINTS,
    ConstructKind.OPTIMIZATION,
    ConstructKind.SHOW,
)


@dataclass
class Construct:
    kind: ConstructKind
    text: str
    """0-based start line of the statement code (not its preceding comment)."""

    start_line: int
    """0-based end line of the statement (inclusive)."""

    end_line: int
    """0-based start of the block including preceding comments (for rewrite)."""

    block_start_line: int
    """Full block text: preceding comments + statement, ready for reorder."""

    block_text: str
    has_preceding_comment: bool


def _code_without_line_comments(stmt: str) -> str:
    """Strip ``%`` line comments for classification; keep code structure."""
    out: list[str] = []
    in_star_block = False
    for line in stmt.split("\n"):
        stripped = line.lstrip()
        if in_star_block:
            if _is_block_close(line):
                in_star_block = False
            continue
        if _is_block_open(line):
            if _is_block_close(line):
                continue
            in_star_block = True
            continue
        if "%" in line:
            code, _, _ = line.partition("%")
            out.append(code)
        else:
            out.append(line)
    return "\n".join(out)


def classify_statement(stmt_text: str) -> ConstructKind:
    code = _code_without_line_comments(stmt_text).strip()
    if not code:
        return ConstructKind.UNKNOWN

    if code.startswith("#const"):
        return ConstructKind.CONSTANTS
    if code.startswith("#include"):
        return ConstructKind.CONSTANTS
    if code.startswith("#show"):
        return ConstructKind.SHOW
    if code.startswith("#minimize") or code.startswith("#maximize"):
        return ConstructKind.OPTIMIZATION
    if code.startswith(":~"):
        return ConstructKind.OPTIMIZATION
    if code.startswith(":-"):
        return ConstructKind.CONSTRAINTS

    if ":-" in code:
        head, _, _ = code.partition(":-")
        if "{" in head:
            return ConstructKind.CHOICES
        return ConstructKind.DEFINITIONS

    if "{" in code:
        return ConstructKind.CHOICES
    return ConstructKind.FACTS


def _statement_code_start_0(stmt_text: str, fragment_start_0: int) -> int:
    """0-based line where actual code begins inside a split fragment.

    Skips leading blanks, ``%`` comments, and ``%*…*%`` blocks that the
    line-based splitter glued onto the statement.
    """
    in_star = False
    for i, line in enumerate(stmt_text.split("\n")):
        if in_star:
            if _is_block_close(line):
                in_star = False
            continue
        if _is_blank(line):
            continue
        if _is_block_open(line):
            if not _is_block_close(line):
                in_star = True
            continue
        if _is_percent_line_comment(line):
            continue
        return fragment_start_0 + i
    return fragment_start_0


def collect_constructs(text: str) -> list[Construct]:
    """Split source into constructs with preceding-comment attachment."""
    lines = text.split("\n")
    constructs: list[Construct] = []

    for stmt_text, fragment_start_0 in _split_top_level_statements(text):
        if not stmt_text.strip():
            continue
        code = _code_without_line_comments(stmt_text).strip()
        if not code or code == ".":
            continue

        kind = classify_statement(stmt_text)
        stmt_line_count = stmt_text.count("\n") + 1
        end_line_0 = fragment_start_0 + stmt_line_count - 1
        code_start_0 = _statement_code_start_0(stmt_text, fragment_start_0)

        preceding = extract_preceding_comment(text, code_start_0 + 1)
        # Also treat comment lines glued into the fragment (above code_start) as preceding
        glued_has_comment = code_start_0 > fragment_start_0 and any(
            _is_percent_line_comment(ln) or _is_block_open(ln)
            for ln in lines[fragment_start_0:code_start_0]
        )
        has_comment = preceding is not None or glued_has_comment

        if preceding is not None:
            block_start = preceding.start_line - 1
        else:
            block_start = fragment_start_0

        block_lines = lines[block_start : end_line_0 + 1]
        block_text = "\n".join(block_lines)

        constructs.append(
            Construct(
                kind=kind,
                text=stmt_text,
                start_line=code_start_0,
                end_line=end_line_0,
                block_start_line=block_start,
                block_text=block_text,
                has_preceding_comment=has_comment,
            )
        )
    return constructs


def find_order_violations(constructs: list[Construct]) -> list[Construct]:
    """Return constructs that appear after a later category already appeared."""
    violations: list[Construct] = []
    highest = -1
    for c in constructs:
        if c.kind == ConstructKind.UNKNOWN:
            continue
        order = int(c.kind)
        if order < highest:
            violations.append(c)
        else:
            highest = order
    return violations


def reorder_constructs(text: str) -> str:
    """Stable-sort construct blocks into expected category order."""
    constructs = collect_constructs(text)
    if not constructs:
        return text

    lines = text.split("\n")

    covered: set[int] = set()
    for c in constructs:
        for i in range(c.block_start_line, c.end_line + 1):
            covered.add(i)

    leading: list[str] = []
    i = 0
    while i < len(lines) and i not in covered:
        leading.append(lines[i])
        i += 1

    last_end = max(c.end_line for c in constructs)
    trailing = lines[last_end + 1 :]

    known = [c for c in constructs if c.kind != ConstructKind.UNKNOWN]
    unknown = [c for c in constructs if c.kind == ConstructKind.UNKNOWN]
    known_sorted = sorted(known, key=lambda c: (int(c.kind), c.start_line))
    ordered = known_sorted + unknown

    parts: list[str] = []
    if leading and any(ln.strip() for ln in leading):
        parts.append("\n".join(leading).rstrip("\n"))
    for c in ordered:
        parts.append(c.block_text.rstrip("\n"))
    body = "\n\n".join(p for p in parts if p is not None and p != "")
    if trailing and any(ln.strip() for ln in trailing):
        trail = "\n".join(trailing).rstrip("\n")
        body = body.rstrip("\n") + "\n\n" + trail
    if text.endswith("\n") and not body.endswith("\n"):
        body += "\n"
    return body
