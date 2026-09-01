from pathlib import Path

from features.diagnostics import build_diagnostics


def test_lone_fact_definition_suppressed():
    text = "bird(tweety)."
    diags = build_diagnostics(text, once_used=True)
    assert not any("used only once" in d.message or "only once" in d.message for d in diags)


def test_two_occurrences_no_once_used_warning():
    # Both bird/1 and ok/0 appear twice so the program is not once-used-noisy.
    text = "bird(tweety).\nok :- bird(X).\nok."
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert diags == []


def test_show_alone_does_not_count_as_use():
    text = "#show bird/1."
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert diags == []


def test_once_used_can_be_disabled():
    text = "ok :- bird(X)."
    diags = build_diagnostics(text, once_used=False)
    assert not any("only once" in d.message for d in diags)


def test_definition_plus_show_no_once_used():
    text = "flies(X) :- bird(X).\nbird(tweety).\n#show flies/1.\n"
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert not any("flies/1" in d.message for d in diags)


def test_definition_plus_maximize_no_once_used():
    text = "reward(X) :- item(X).\nitem(a).\n#maximize { 1, X : reward(X) }.\n"
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert not any("reward/1" in d.message for d in diags)


def test_lone_definition_suppressed():
    text = "label(hello).\n"
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert diags == []


def test_lone_body_use_warns():
    text = "ok :- bird(X).\n"
    diags = [
        d
        for d in build_diagnostics(text, once_used=True)
        if "bird/1" in d.message and "only once" in d.message
    ]
    assert len(diags) == 1
    assert "typo" in diags[0].message.lower() or "definition" in diags[0].message.lower()


def test_example_test_lp_once_used_bound():
    text = (Path(__file__).resolve().parents[2] / "examples" / "test.lp").read_text()
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert len(diags) <= 5


def test_once_used_weak_constraint_message():
    text = ":~ lonely(X). [1, X]"
    diags = [d for d in build_diagnostics(text, once_used=True) if "only once" in d.message]
    assert len(diags) == 1
    assert "weak constraint" in diags[0].message
