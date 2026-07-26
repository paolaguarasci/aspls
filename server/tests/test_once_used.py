from features.diagnostics import build_diagnostics


def test_single_occurrence_warns():
    text = "bird(tweety)."
    diags = build_diagnostics(text, once_used=True)
    assert any("used only once" in d.message for d in diags)


def test_two_occurrences_no_once_used_warning():
    # Both bird/1 and ok/0 appear twice so the program is not once-used-noisy.
    text = "bird(tweety).\nok :- bird(X).\nok."
    diags = [d for d in build_diagnostics(text, once_used=True) if "used only once" in d.message]
    assert diags == []


def test_show_alone_does_not_count_as_use():
    text = "#show bird/1."
    diags = [d for d in build_diagnostics(text, once_used=True) if "used only once" in d.message]
    assert diags == []


def test_once_used_can_be_disabled():
    text = "bird(tweety)."
    diags = build_diagnostics(text, once_used=False)
    assert not any("used only once" in d.message for d in diags)
