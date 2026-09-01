from pathlib import Path
from parser import parse_document

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_facts_and_rules_without_errors():
    text = (FIXTURES / "facts_and_rules.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_reports_syntax_error_with_position():
    text = "bird(tweety)\npenguin(pingu)."  # missing dot after first fact
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.errors[0].line == 2


def test_parses_disjunction_aggregates_and_directives():
    text = (FIXTURES / "disjunction_aggregates_directives.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_comparison_literals_in_body():
    text = (FIXTURES / "comparison_literals.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_recovers_after_one_bad_statement_and_parses_the_rest():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.tree is not None
    assert len(result.tree.children) == 2  # bird(tweety). and penguin(pingu).


def test_error_line_number_matches_original_document():
    text = "bird(tweety).\nbad statement here\npenguin(pingu)."
    result = parse_document(text)
    assert result.errors[0].line == 2


def test_multiline_bad_statement_produces_one_error():
    text = "bird(tweety).\nbad statement\nspanning lines\npenguin(pingu)."
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.errors[0].line == 2
    assert result.tree is not None
    assert len(result.tree.children) == 2


def test_large_unparseable_fragment_does_not_crash():
    text = "\n".join(f"not a valid line {i}" for i in range(2000))
    result = parse_document(text)
    assert len(result.errors) == 1
    assert result.errors[0].line == 1
    assert result.tree is None


def test_parses_choice_rules():
    text = (FIXTURES / "choice_rules.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_choice_syntax_error_reports_line():
    text = "1 { chosen(X) : candidate(X) 1.\n"  # missing closing }
    result = parse_document(text)
    assert len(result.errors) >= 1
    assert result.errors[0].line >= 1


def test_parses_weak_constraints():
    text = (FIXTURES / "weak_constraints.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_include_directive():
    text = (FIXTURES / "include_main.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_external_directive():
    text = (FIXTURES / "external_directive.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_minimize_directive():
    text = (FIXTURES / "minimize_directive.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_heuristic_directive():
    text = (FIXTURES / "heuristic_directive.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_program_directive():
    text = (FIXTURES / "program_directive.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_parses_script_directive():
    text = (FIXTURES / "script_directive.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None
    assert len(result.tree.children) == 2  # script block + p(a).


def test_script_directive_tolerates_dots_in_lua_body():
    text = """#script(lua)
local t = "a.b.c"
function main(prg) prg:solve() end
#end.
fact(x).
"""
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None
    assert len(result.tree.children) == 2


def test_parses_aggregates():
    text = (FIXTURES / "aggregates.lp").read_text()
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_weak_constraint_syntax_error_reports_line():
    # Weight bracket missing closing ]
    text = ":~ selected(X). [1@1, X\n"
    result = parse_document(text)
    assert len(result.errors) >= 1
    # EOF after unclosed '[' — Lark may report line -1; assert bracket error, not unknown :~
    assert "RSQB" in result.errors[0].message


def test_parses_choice_rules_with_variable_bounds():
    text = "size(N).\nlimit(M).\nN { chosen(X) : candidate(X) } M :- size(N), limit(M).\n"
    result = parse_document(text)
    assert result.errors == []
    assert result.tree is not None


def test_tutorial_examples_parse():
  """Every .lp file under examples/*/ must parse without errors."""
  examples = Path(__file__).resolve().parents[2] / "examples"
  paths = sorted(examples.glob("*/*.lp"))
  assert paths, "expected tutorial .lp files under examples/*/"
  for path in paths:
    result = parse_document(path.read_text())
    assert result.errors == [], f"{path.relative_to(examples.parent)}: {result.errors}"


def test_cookbook_choice_and_weak_recipes_parse():
    """Recipes that previously red-squiggled must parse clean."""
    samples = [
        # choice-exact-one (body without surrounding comments)
        "candidate(1).\ncandidate(2).\n1 { chosen(X) : candidate(X) } 1.\n",
        # constraints-integrity
        "{ a; b }.\n:- a, b.\n",
        # optimization-weak
        "item(a).\n{ selected(X) : item(X) }.\n:~ selected(X), expensive(X). [1@1, X]\n",
    ]
    for text in samples:
        result = parse_document(text)
        assert result.errors == [], text
