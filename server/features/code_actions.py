"""Code actions for learner-mode quick fixes."""

from __future__ import annotations

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    Diagnostic,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)

from constructs import find_order_violations, collect_constructs, reorder_constructs
from features.diagnostics import CODE_RULE_ORDER


def _has_rule_order_diagnostic(diagnostics: list[Diagnostic] | None) -> bool:
    if not diagnostics:
        return False
    return any(d.code == CODE_RULE_ORDER for d in diagnostics)


def build_fix_order_action(uri: str, text: str) -> CodeAction | None:
    """Return a Fix Order workspace edit when the document has order violations."""
    if not find_order_violations(collect_constructs(text)):
        return None

    new_text = reorder_constructs(text)
    if new_text == text:
        return None

    lines = text.split("\n")
    end_line = max(len(lines) - 1, 0)
    end_char = len(lines[-1]) if lines else 0
    edit = TextEdit(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=end_line, character=end_char),
        ),
        new_text=new_text,
    )
    return CodeAction(
        title="Fix Order",
        kind=CodeActionKind.QuickFix,
        edit=WorkspaceEdit(changes={uri: [edit]}),
        is_preferred=True,
    )


def build_code_actions(
    uri: str,
    text: str,
    *,
    learner_mode: bool = False,
    diagnostics: list[Diagnostic] | None = None,
) -> list[CodeAction]:
    if not learner_mode:
        return []
    # Offer Fix Order when context diagnostics include rule-order, or when
    # the document itself currently has order violations (context may be empty).
    if diagnostics is not None and not _has_rule_order_diagnostic(diagnostics):
        if not find_order_violations(collect_constructs(text)):
            return []
    action = build_fix_order_action(uri, text)
    return [action] if action is not None else []
