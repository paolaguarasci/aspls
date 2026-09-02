from features.diagnostics import CODE_PARSER_SYNTAX, build_diagnostics


def test_valid_document_has_no_diagnostics():
    # Both bird/1 and ok/0 appear twice so once-used does not fire.
    text = "bird(tweety).\nok :- bird(X).\nok."
    diagnostics = build_diagnostics(text, once_used=True)
    assert diagnostics == []


def test_invalid_document_has_one_diagnostic_at_correct_line():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    diagnostics = build_diagnostics(text)
    assert len(diagnostics) == 1
    assert diagnostics[0].range.start.line == 1  # 0-indexed for LSP; parser reports line 2 (1-indexed)
    assert diagnostics[0].code == CODE_PARSER_SYNTAX


def test_diagnostics_include_unsafe_variables():
    text = "flies(X) :- bird(Y)."
    diagnostics = build_diagnostics(text)
    assert any(
        d.source == "aspls" and "Unsafe variable" in d.message for d in diagnostics
    )
