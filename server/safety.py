from __future__ import annotations

from dataclasses import dataclass

import lark


@dataclass
class UnsafeFinding:
    line: int
    column: int
    variables: list[str]


def _collect_vars(node, out: list[tuple[str, int, int]], *, under_negation: bool = False) -> None:
    if isinstance(node, lark.Token):
        # Bare VARIABLE in range_bound (grammar: INT | IDENTIFIER | VARIABLE).
        if node.type == "VARIABLE":
            out.append((str(node), node.line, node.column))
        return
    if not isinstance(node, lark.Tree):
        return
    if node.data == "var_term":
        tok = node.children[0]
        out.append((str(tok), tok.line, tok.column))
        return
    if node.data == "negated_literal":
        for child in node.children:
            _collect_vars(child, out, under_negation=True)
        return
    for child in node.children:
        _collect_vars(child, out, under_negation=under_negation)


def _collect_positive_atom_vars(node, out: set[str]) -> None:
    """Variables appearing in positive ordinary atoms (not under not, not comparisons)."""
    if not isinstance(node, lark.Tree):
        return
    if node.data == "negated_literal":
        return
    if node.data in ("compound_atom", "nullary_atom"):
        vars_here: list[tuple[str, int, int]] = []
        _collect_vars(node, vars_here)
        for name, _, _ in vars_here:
            out.add(name)
        return
    if node.data in (
        "aggregate",
        "aggregate_cmp_term",
        "term_cmp_aggregate",
        "term_cmp_term",
        "comparison",
    ):
        # Comparisons / aggregates do not bind for our simplified safety rule.
        return
    for child in node.children:
        _collect_positive_atom_vars(child, out)


def _finding_for_vars(var_occurrences: list[tuple[str, int, int]], unsafe: set[str]) -> UnsafeFinding | None:
    if not unsafe:
        return None
    ordered = sorted(unsafe)
    for name, line, column in var_occurrences:
        if name in unsafe:
            return UnsafeFinding(line=line, column=column, variables=ordered)
    return UnsafeFinding(line=1, column=1, variables=ordered)


def _check_rule_or_constraint(statement: lark.Tree) -> UnsafeFinding | None:
    all_vars: list[tuple[str, int, int]] = []
    safe: set[str] = set()
    if statement.data == "rule":
        head, body = statement.children[0], statement.children[1]
        _collect_vars(head, all_vars)
        _collect_vars(body, all_vars)
        _collect_positive_atom_vars(body, safe)
    elif statement.data == "constraint":
        body = statement.children[0]
        _collect_vars(body, all_vars)
        _collect_positive_atom_vars(body, safe)
    elif statement.data == "fact":
        head = statement.children[0]
        _collect_vars(head, all_vars)
        # Facts have no body binders.
        safe = set()
    else:
        return None
    names = {n for n, _, _ in all_vars}
    return _finding_for_vars(all_vars, names - safe)


def find_unsafe_variables(tree: lark.Tree | None) -> list[UnsafeFinding]:
    if tree is None:
        return []
    findings: list[UnsafeFinding] = []
    for statement_wrapper in tree.children:
        statement = statement_wrapper.children[0]
        # Unwrap fact/rule/constraint aliases from grammar rule names
        data = statement.data
        if data in ("fact", "rule", "constraint"):
            found = _check_rule_or_constraint(statement)
            if found:
                findings.append(found)
    return findings
