from lsprotocol.types import DiagnosticSeverity

from features.diagnostics import (
    CODE_MISSING_COMMENT,
    CODE_RULE_ORDER,
    build_diagnostics,
)


def test_learner_mode_off_by_default():
    text = "#show bird/1.\nbird(tweety)."
    diags = build_diagnostics(text, once_used=False, learner_mode=False)
    assert not any(d.code in (CODE_RULE_ORDER, CODE_MISSING_COMMENT) for d in diags)


def test_learner_mode_rule_order_warning():
    text = "% show first\n#show bird/1.\n% a bird\nbird(tweety)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    order = [d for d in diags if d.code == CODE_RULE_ORDER]
    assert len(order) == 1
    assert "Recommended order" in order[0].message
    assert "Fix Order" in order[0].message


def test_learner_mode_missing_comment_warning():
    text = "bird(tweety).\nflies(X) :- bird(X)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    missing = [d for d in diags if d.code == CODE_MISSING_COMMENT]
    assert len(missing) == 2
    assert all("Add a % comment" in d.message for d in missing)
    assert all("Add preceding comment" in d.message for d in missing)


def test_learner_mode_no_missing_comment_when_documented():
    text = "% a bird\nbird(tweety).\n% flies if bird\nflies(X) :- bird(X)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    missing = [d for d in diags if d.code == CODE_MISSING_COMMENT]
    assert missing == []


def test_learner_severity_is_information():
    text = "#show bird/1.\nbird(tweety)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    learner = [d for d in diags if d.code in (CODE_RULE_ORDER, CODE_MISSING_COMMENT)]
    assert learner
    assert all(d.severity == DiagnosticSeverity.Information for d in learner)


def test_learner_messages_mention_quick_fix():
    text = "#show bird/1.\nbird(tweety)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    order = [d for d in diags if d.code == CODE_RULE_ORDER]
    missing = [d for d in diags if d.code == CODE_MISSING_COMMENT]
    assert order and "Fix Order" in order[0].message
    assert missing and "Add preceding comment" in missing[0].message
