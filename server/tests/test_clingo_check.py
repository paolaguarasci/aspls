from clingo_check import check_with_clingo


def test_returns_empty_list_when_clingo_not_installed_or_program_is_safe():
    # This test asserts the no-op contract holds regardless of whether clingo
    # is installed in the dev environment: a safe program produces no findings,
    # and an absent clingo module must never raise.
    text = "bird(tweety)."
    result = check_with_clingo(text)
    assert result == []
