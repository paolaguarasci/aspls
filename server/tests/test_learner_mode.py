from lsprotocol.types import DiagnosticSeverity

from features.diagnostics import (
    CODE_MISSING_COMMENT,
    CODE_RULE_ORDER,
    build_diagnostics,
)
from features.learner_hints import CODE_NAMING, CODE_SAFETY, CODE_UNSAFE_VARIABLE


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


def test_learner_safety_hint_head_variable():
    text = "flies(X) :- bird(Y)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    safety = [d for d in diags if d.code == CODE_SAFETY]
    assert len(safety) == 1
    assert "Safety" in safety[0].message
    assert "head" in safety[0].message.lower()
    assert safety[0].severity == DiagnosticSeverity.Information


def test_learner_safety_hint_negation_only():
    text = "ok :- not bird(X)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    safety = [d for d in diags if d.code == CODE_SAFETY]
    assert len(safety) == 1
    assert "negation" in safety[0].message.lower()


def test_learner_unsafe_variable_hint_fact():
    text = "bird(X)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    unsafe = [d for d in diags if d.code == CODE_UNSAFE_VARIABLE]
    assert len(unsafe) == 1
    assert "ground" in unsafe[0].message.lower()


def test_learner_naming_hint_camel_case_predicate():
    text = "myPredicate(X) :- bird(X)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    naming = [d for d in diags if d.code == CODE_NAMING]
    assert len(naming) == 1
    assert "snake_case" in naming[0].message
    assert "my_predicate" in naming[0].message


def test_learner_new_hints_off_by_default():
    text = "flies(X) :- bird(Y).\nmyPredicate(X) :- bird(X)."
    diags = build_diagnostics(text, once_used=False, learner_mode=False)
    codes = {d.code for d in diags if d.code}
    assert CODE_SAFETY not in codes
    assert CODE_UNSAFE_VARIABLE not in codes
    assert CODE_NAMING not in codes


def test_learner_unsafe_errors_still_emitted_with_learner_mode():
    text = "flies(X) :- bird(Y)."
    diags = build_diagnostics(text, once_used=False, learner_mode=True)
    errors = [d for d in diags if d.severity == DiagnosticSeverity.Error]
    assert any("Unsafe variable" in d.message for d in errors)
