from server import is_config_file_change


def test_is_config_file_change_matches_basename():
    assert is_config_file_change(
        "file:///proj/aspls.clingo.json",
        "aspls.clingo.json",
    )


def test_is_config_file_change_rejects_other_files():
    assert not is_config_file_change(
        "file:///proj/other.json",
        "aspls.clingo.json",
    )


def test_is_config_file_change_respects_custom_name():
    assert is_config_file_change(
        "file:///proj/my-clingo.json",
        "my-clingo.json",
    )
    assert not is_config_file_change(
        "file:///proj/aspls.clingo.json",
        "my-clingo.json",
    )
