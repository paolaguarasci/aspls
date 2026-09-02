"""Document formatting by construct order (learner-mode reorder logic)."""

from __future__ import annotations

from lsprotocol.types import Position, Range, TextEdit

from constructs import collect_constructs, find_order_violations, reorder_constructs


def build_format_edits(text: str) -> list[TextEdit] | None:
    """Return a full-document edit reordering constructs, or None if unchanged."""
    if not find_order_violations(collect_constructs(text)):
        return None

    new_text = reorder_constructs(text)
    if new_text == text:
        return None

    lines = text.split("\n")
    end_line = max(len(lines) - 1, 0)
    end_char = len(lines[-1]) if lines else 0
    return [
        TextEdit(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=end_line, character=end_char),
            ),
            new_text=new_text,
        )
    ]
