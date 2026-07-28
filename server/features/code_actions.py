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
from features.diagnostics import CODE_MISSING_COMMENT, CODE_RULE_ORDER

COMMENT_STUB = "% Describe this statement"


def _has_rule_order_diagnostic(diagnostics: list[Diagnostic] | None) -> bool:
    if not diagnostics:
        return False
    return any(d.code == CODE_RULE_ORDER for d in diagnostics)


def _missing_comment_diagnostics(
    diagnostics: list[Diagnostic] | None,
) -> list[Diagnostic]:
    if not diagnostics:
        return []
    return [d for d in diagnostics if d.code == CODE_MISSING_COMMENT]


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


def build_add_preceding_comment_action(
    uri: str, text: str, *, line: int
) -> CodeAction | None:
    """Insert a didactic comment stub above ``line`` (0-based)."""
    if line < 0:
        return None
    lines = text.split("\n")
    if line > len(lines):
        return None
    # Already has a stub/comment on the previous line — skip.
    if line > 0 and lines[line - 1].lstrip().startswith("%"):
        return None

    insert = COMMENT_STUB + "\n"
    edit = TextEdit(
        range=Range(
            start=Position(line=line, character=0),
            end=Position(line=line, character=0),
        ),
        new_text=insert,
    )
    return CodeAction(
        title="Add preceding comment",
        kind=CodeActionKind.QuickFix,
        edit=WorkspaceEdit(changes={uri: [edit]}),
        diagnostics=None,
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

    actions: list[CodeAction] = []

    offer_fix_order = True
    if diagnostics is not None and not _has_rule_order_diagnostic(diagnostics):
        if not find_order_violations(collect_constructs(text)):
            offer_fix_order = False
    if offer_fix_order:
        action = build_fix_order_action(uri, text)
        if action is not None:
            actions.append(action)

    missing = _missing_comment_diagnostics(diagnostics)
    if diagnostics is None:
        # No context: offer stubs for undocumented constructs.
        for c in collect_constructs(text):
            if c.has_preceding_comment:
                continue
            action = build_add_preceding_comment_action(uri, text, line=c.start_line)
            if action is not None:
                actions.append(action)
    else:
        seen_lines: set[int] = set()
        for d in missing:
            line = d.range.start.line
            if line in seen_lines:
                continue
            seen_lines.add(line)
            action = build_add_preceding_comment_action(uri, text, line=line)
            if action is not None:
                actions.append(action)

    return actions
