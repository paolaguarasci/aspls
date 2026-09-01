from features.signature_help import build_signature_help


def test_signature_help_with_docstring():
    text = (
        "%*\n"
        "#edge(A, B).\n"
        "\n"
        "Directed edge.\n"
        "\n"
        "#parameters\n"
        "    - A : Source node.\n"
        "    - B : Target node.\n"
        "*%\n"
        "edge(1, 2).\n"
    )
    # cursor inside first argument
    result = build_signature_help(text, line=9, column=5)
    assert result is not None
    assert len(result.signatures) == 1
    sig = result.signatures[0]
    assert sig.label == "edge(A, B)."
    assert sig.documentation is not None
    assert "Directed edge" in sig.documentation.value
    assert len(sig.parameters) == 2
    assert sig.parameters[0].label == "A"
    assert "Source node" in sig.parameters[0].documentation.value
    assert sig.parameters[1].label == "B"
    assert result.active_parameter == 0


def test_signature_help_active_parameter_second_arg():
    text = (
        "%*\n"
        "#edge(A, B).\n"
        "\n"
        "Directed edge.\n"
        "*%\n"
        "edge(1, 2).\n"
    )
    # cursor on '2' in edge(1, 2).
    result = build_signature_help(text, line=5, column=8)
    assert result is not None
    assert result.active_parameter == 1


def test_signature_help_without_docstring_synthesizes_signature():
    text = "bird(tweety).\n"
    result = build_signature_help(text, line=0, column=5)
    assert result is not None
    sig = result.signatures[0]
    assert sig.label == "bird(X1)."
    assert sig.documentation is None
    assert len(sig.parameters) == 1
    assert sig.parameters[0].label == "X1"


def test_signature_help_on_predicate_name():
    text = "bird(tweety).\n"
    result = build_signature_help(text, line=0, column=2)
    assert result is not None
    sig = result.signatures[0]
    assert sig.label == "bird(X1)."
    assert result.active_parameter is None


def test_signature_help_outside_predicate_returns_none():
    text = "bird(tweety).\n"
    result = build_signature_help(text, line=5, column=0)
    assert result is None
