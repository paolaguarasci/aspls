"""Learner-mode Information hints: unbound variables, safety, naming."""

from __future__ import annotations

import re

import lark
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from parser import parse_document
from safety import (
    _check_rule_or_constraint,
    _check_weak_constraint,
    _collect_vars,
)
from symbols import collect_occurrences

CODE_UNSAFE_VARIABLE = "learner.unsafeVariable"
CODE_SAFETY = "learner.safety"
CODE_NAMING = "learner.naming"

_CAMEL_CASE_PREDICATE = re.compile(r"^[a-z]+[A-Z]")


def _diag(
    line: int,
    column: int,
    length: int,
    message: str,
    code: str,
) -> Diagnostic:
    lsp_line = max(line - 1, 0)
    lsp_col = max(column - 1, 0)
    return Diagnostic(
        range=Range(
            start=Position(line=lsp_line, character=lsp_col),
            end=Position(line=lsp_line, character=lsp_col + max(length, 1)),
        ),
        message=message,
        severity=DiagnosticSeverity.Information,
        source="aspls",
        code=code,
    )


def _vars_under_negation_only(body: lark.Tree, names: set[str]) -> set[str]:
    """Variables that appear only inside negated literals in the body."""
    negated: set[str] = set()
    positive: set[str] = set()

    def walk(node, *, under_negation: bool = False) -> None:
        if isinstance(node, lark.Token):
            if node.type == "VARIABLE":
                (negated if under_negation else positive).add(str(node))
            return
        if not isinstance(node, lark.Tree):
            return
        if node.data == "var_term":
            tok = node.children[0]
            (negated if under_negation else positive).add(str(tok))
            return
        if node.data == "negated_literal":
            for child in node.children:
                walk(child, under_negation=True)
            return
        for child in node.children:
            walk(child, under_negation=under_negation)

    walk(body)
    return names & (negated - positive)


def _head_vars(statement: lark.Tree) -> set[str]:
    if statement.data not in ("rule", "fact"):
        return set()
    head = statement.children[0]
    found: list[tuple[str, int, int]] = []
    _collect_vars(head, found)
    return {name for name, _, _ in found}


def _learner_hint_for_unsafe(statement: lark.Tree, finding) -> Diagnostic | None:
    unsafe = set(finding.variables)
    if not unsafe:
        return None

    name = finding.variables[0]
    line = finding.line
    column = finding.column
    length = len(name)

    if statement.data == "fact":
        return _diag(
            line,
            column,
            length,
            (
                f"Variable {name} in a fact must be ground (no free variables). "
                "Replace it with a constant or use a rule with a body."
            ),
            CODE_UNSAFE_VARIABLE,
        )

    body = None
    if statement.data in ("rule", "constraint"):
        body = statement.children[0] if statement.data == "constraint" else statement.children[1]
    elif statement.data == "weak_constraint":
        body = statement.children[0]

    head = _head_vars(statement)
    head_unbound = unsafe & head
    if head_unbound and body is not None:
        var = sorted(head_unbound)[0]
        return _diag(
            line,
            column,
            len(var),
            (
                f"Safety: variable {var} in the rule head must be bound in the body "
                "(appear in a positive atom, e.g. bird(X))."
            ),
            CODE_SAFETY,
        )

    if body is not None:
        neg_only = _vars_under_negation_only(body, unsafe)
        if neg_only:
            var = sorted(neg_only)[0]
            return _diag(
                line,
                column,
                len(var),
                (
                    f"Safety: variable {var} appears only under negation. "
                    "Bind it first in a positive literal (e.g. bird(X), not penguin(X))."
                ),
                CODE_SAFETY,
            )

    vars_list = ", ".join(finding.variables)
    return _diag(
        line,
        column,
        length,
        (
            f"Unbound variable{'s' if len(finding.variables) > 1 else ''}: {vars_list}. "
            "Every variable must be bound by a positive literal in the body."
        ),
        CODE_UNSAFE_VARIABLE,
    )


def _unsafe_variable_hints(tree: lark.Tree | None) -> list[Diagnostic]:
    if tree is None:
        return []
    hints: list[Diagnostic] = []
    for statement_wrapper in tree.children:
        statement = statement_wrapper.children[0]
        data = statement.data
        found = None
        if data in ("fact", "rule", "constraint"):
            found = _check_rule_or_constraint(statement)
        elif data == "weak_constraint":
            found = _check_weak_constraint(statement)
        if found is None:
            continue
        hint = _learner_hint_for_unsafe(statement, found)
        if hint is not None:
            hints.append(hint)
    return hints


def _naming_hints(tree: lark.Tree | None) -> list[Diagnostic]:
    if tree is None:
        return []
    hints: list[Diagnostic] = []
    seen: set[tuple[str, int, int]] = set()
    for occ in collect_occurrences(tree):
        if not _CAMEL_CASE_PREDICATE.match(occ.name):
            continue
        key = (occ.name, occ.line, occ.column)
        if key in seen:
            continue
        seen.add(key)
        snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", occ.name).lower()
        hints.append(
            _diag(
                occ.line,
                occ.column,
                len(occ.name),
                (
                    f"Naming: predicate '{occ.name}' uses camelCase; "
                    f"prefer snake_case (e.g. {snake})."
                ),
                CODE_NAMING,
            )
        )
    return hints


def build_learner_hints(text: str, tree: lark.Tree | None = None) -> list[Diagnostic]:
    """Information hints for learner mode: safety, unbound vars, naming."""
    if tree is None:
        tree = parse_document(text).tree
    hints = _unsafe_variable_hints(tree)
    hints.extend(_naming_hints(tree))
    return hints
