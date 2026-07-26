from features.code_actions import build_code_actions, build_fix_order_action
from features.diagnostics import CODE_RULE_ORDER, build_diagnostics
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
    assert len(actions) == 1
    assert actions[0].title == "Fix Order"


def test_code_actions_with_rule_order_diagnostic_context():
    text = "#show bird/1.\nbird(tweety)."
    diags = [
        Diagnostic(
            range=Range(start=Position(0, 0), end=Position(0, 1)),
            message="order",
            severity=DiagnosticSeverity.Warning,
            code=CODE_RULE_ORDER,
        )
    ]
    actions = build_code_actions(
        "file:///tmp/t.lp", text, learner_mode=True, diagnostics=diags
    )
    assert len(actions) == 1


def test_no_fix_order_when_already_sorted():
    text = "% a bird\nbird(tweety).\n% show\n#show bird/1.\n"
    assert build_fix_order_action("file:///tmp/t.lp", text) is None
    assert (
        build_code_actions("file:///tmp/t.lp", text, learner_mode=True) == []
    )


def test_diagnostics_and_fix_order_roundtrip():
    text = "#show bird/1.\nbird(tweety)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    assert any(d.code == CODE_RULE_ORDER for d in diags)
    action = build_fix_order_action("file:///tmp/t.lp", text)
    new_text = action.edit.changes["file:///tmp/t.lp"][0].new_text
    after = build_diagnostics(new_text, once_used=False, learner_mode=True)
    assert not any(d.code == CODE_RULE_ORDER for d in after)
