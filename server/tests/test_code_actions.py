from features.code_actions import (
    COMMENT_STUB,
    build_add_preceding_comment_action,
    build_code_actions,
    build_fix_order_action,
)
from features.diagnostics import CODE_MISSING_COMMENT, CODE_RULE_ORDER, build_diagnostics
from constructs import collect_constructs, find_order_violations
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range


def test_fix_order_action_reorders():
    text = "#show bird/1.\n% a bird\nbird(tweety).\n"
    action = build_fix_order_action("file:///tmp/t.lp", text)
    assert action is not None
    assert action.title == "Fix Order"
    assert action.edit is not None
    edits = action.edit.changes["file:///tmp/t.lp"]
    assert len(edits) == 1
    new_text = edits[0].new_text
    assert find_order_violations(collect_constructs(new_text)) == []
    assert new_text.index("bird(tweety)") < new_text.index("#show")


def test_code_actions_gated_by_learner_mode():
    text = "#show bird/1.\nbird(tweety)."
    assert build_code_actions("file:///tmp/t.lp", text, learner_mode=False) == []
    actions = build_code_actions("file:///tmp/t.lp", text, learner_mode=True)
    titles = [a.title for a in actions]
    assert "Fix Order" in titles
    assert "Add preceding comment" in titles


def test_code_actions_with_rule_order_diagnostic_context():
    text = "#show bird/1.\nbird(tweety)."
    diags = [
        Diagnostic(
            range=Range(start=Position(0, 0), end=Position(0, 1)),
            message="order",
            severity=DiagnosticSeverity.Information,
            code=CODE_RULE_ORDER,
        )
    ]
    actions = build_code_actions(
        "file:///tmp/t.lp", text, learner_mode=True, diagnostics=diags
    )
    assert len(actions) == 1
    assert actions[0].title == "Fix Order"


def test_no_fix_order_when_already_sorted():
    text = "% a bird\nbird(tweety).\n% show\n#show bird/1.\n"
    assert build_fix_order_action("file:///tmp/t.lp", text) is None
    assert build_code_actions("file:///tmp/t.lp", text, learner_mode=True) == []


def test_diagnostics_and_fix_order_roundtrip():
    text = "#show bird/1.\nbird(tweety)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    assert any(d.code == CODE_RULE_ORDER for d in diags)
    action = build_fix_order_action("file:///tmp/t.lp", text)
    new_text = action.edit.changes["file:///tmp/t.lp"][0].new_text
    after = build_diagnostics(new_text, once_used=False, learner_mode=True)
    assert not any(d.code == CODE_RULE_ORDER for d in after)


def test_add_preceding_comment_quick_fix():
    text = "bird(tweety).\n"
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    missing = [d for d in diags if d.code == CODE_MISSING_COMMENT]
    assert missing
    actions = build_code_actions(
        "file:///tmp/t.lp", text, learner_mode=True, diagnostics=missing
    )
    titles = [a.title for a in actions]
    assert "Add preceding comment" in titles
    action = next(a for a in actions if a.title == "Add preceding comment")
    # Apply insert edit to full document
    edit = action.edit.changes["file:///tmp/t.lp"][0]
    assert edit.range.start.line == 0
    assert edit.new_text == COMMENT_STUB + "\n"
    new_text = edit.new_text + text
    assert new_text.startswith(COMMENT_STUB + "\n")
    after = build_diagnostics(new_text, once_used=False, learner_mode=True)
    assert not any(d.code == CODE_MISSING_COMMENT for d in after)


def test_add_preceding_comment_action_helper():
    text = "bird(tweety).\n"
    action = build_add_preceding_comment_action("file:///tmp/t.lp", text, line=0)
    assert action is not None
    assert action.title == "Add preceding comment"
