from features.diagnostics import build_diagnostics


def test_valid_document_has_no_diagnostics():
    text = "bird(tweety)."
    diagnostics = build_diagnostics(text)
    assert diagnostics == []


def test_invalid_document_has_one_diagnostic_at_correct_line():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    diagnostics = build_diagnostics(text)
    assert len(diagnostics) == 1
    assert diagnostics[0].range.start.line == 1  # 0-indexed for LSP; parser reports line 2 (1-indexed)
