"""Extract preceding comments from ASP source text.

Lark ignores COMMENT tokens, so features that need comments must scan raw source.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrecedingComment:
    """Comment block immediately above ``statement_line`` (1-based)."""

    text: str
    """Comment body with leading ``%`` / ``%*`` markers stripped per line."""

    raw: str
    """Original comment lines including markers, joined by newlines."""

    start_line: int
    """1-based first comment line."""

    end_line: int
    """1-based last comment line (inclusive)."""


def _strip_line_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("%*"):
        body = stripped[2:]
        if body.rstrip().endswith("*%"):
            body = body.rstrip()[:-2]
        return body.strip()
    if stripped.startswith("%"):
        return stripped[1:].lstrip()
    return stripped


def _is_percent_line_comment(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("%")


def _is_blank(line: str) -> bool:
    return not line.strip()


def _is_block_close(line: str) -> bool:
    return line.rstrip().endswith("*%") or line.strip() == "*%"


def _is_block_open(line: str) -> bool:
    return line.lstrip().startswith("%*")


def _extract_percent_star_block(
    lines: list[str], end_idx: int
) -> tuple[int, int] | None:
    """If ``lines[end_idx]`` closes a ``%*…*%`` block, return (start_idx, end_idx)."""
    if end_idx < 0 or end_idx >= len(lines):
        return None
    if not _is_block_close(lines[end_idx]):
        return None
    # Single-line ``%* ... *%``
    if _is_block_open(lines[end_idx]):
        return end_idx, end_idx
    for i in range(end_idx - 1, -1, -1):
        if _is_block_open(lines[i]):
            return i, end_idx
    return None


def extract_preceding_comment(text: str, statement_line: int) -> PrecedingComment | None:
    """Return contiguous comment lines immediately above ``statement_line`` (1-based).

    Recognizes:
    - Contiguous ``%`` line comments
    - Multi-line ``%* … *%`` docstring blocks (middle lines need not start with ``%``)
    """
    if statement_line < 1:
        return None
    lines = text.split("\n")
    idx = statement_line - 2  # 0-based index of line above statement
    while idx >= 0 and _is_blank(lines[idx]):
        idx -= 1
    if idx < 0:
        return None

    # Prefer %* ... *% block ending on this line
    block = _extract_percent_star_block(lines, idx)
    if block is not None:
        start_idx, end_idx = block
    elif _is_percent_line_comment(lines[idx]):
        end_idx = idx
        start_idx = idx
        while start_idx > 0 and _is_percent_line_comment(lines[start_idx - 1]):
            start_idx -= 1
        # If the contiguous run is actually a %* block open without us detecting
        # close on end — still treat % lines as comments.
    else:
        return None

    block_lines = lines[start_idx : end_idx + 1]
    raw = "\n".join(block_lines)

    # Body: strip markers
    if _is_block_open(block_lines[0]) and _is_block_close(block_lines[-1]):
        inner = block_lines[:]
        # Strip opener from first line
        first = inner[0].lstrip()
        if first.startswith("%*"):
            first_rest = first[2:]
            if len(inner) == 1 and first_rest.rstrip().endswith("*%"):
                first_rest = first_rest.rstrip()[:-2]
            inner[0] = first_rest
        if len(inner) > 1:
            last = inner[-1]
            if last.rstrip().endswith("*%"):
                inner[-1] = last.rstrip()[:-2].rstrip()
        text_body = "\n".join(ln.rstrip() for ln in inner).strip()
    else:
        body_lines = [_strip_line_comment(l) for l in block_lines]
        text_body = "\n".join(body_lines).strip()

    return PrecedingComment(
        text=text_body,
        raw=raw,
        start_line=start_idx + 1,
        end_line=end_idx + 1,
    )


def has_preceding_comment(text: str, statement_line: int) -> bool:
    return extract_preceding_comment(text, statement_line) is not None


def first_code_line_1based(stmt_text: str, fragment_start_0: int) -> int:
    """1-based line of the first non-comment, non-blank line in a statement fragment."""
    for i, line in enumerate(stmt_text.split("\n")):
        if _is_blank(line) or _is_percent_line_comment(line):
            continue
        # Inside %* block continuation (no leading %): skip until after *%
        # For fragments that start with %*, skip until after closer.
        return fragment_start_0 + i + 1
    return fragment_start_0 + 1


def line_at(text: str, line_1based: int) -> str:
    """Return the 1-based line contents, or empty string if out of range."""
    lines = text.split("\n")
    if line_1based < 1 or line_1based > len(lines):
        return ""
    return lines[line_1based - 1]
