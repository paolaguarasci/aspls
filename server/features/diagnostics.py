from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from constructs import (
    KIND_LABELS,
    collect_constructs,
    find_order_violations,
)
from parser import parse_document
from clingo_check import check_with_clingo
from features.learner_hints import build_learner_hints
from safety import find_unsafe_variables
from symbols import DEFINING_ROLES, DIRECTIVE_ROLES, build_symbol_index

CODE_RULE_ORDER = "learner.ruleOrder"
CODE_MISSING_COMMENT = "learner.missingComment"


def _learner_diagnostics(text: str, tree=None) -> list[Diagnostic]:
    constructs = collect_constructs(text)
    diagnostics: list[Diagnostic] = []

    for c in find_order_violations(constructs):
        label = KIND_LABELS.get(c.kind, "construct")
        line = c.start_line
        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=0),
                    end=Position(line=line, character=max(len(c.text.split("\n")[0]), 1)),
                ),
                message=(
                    f"Recommended order: move this {label} before later categories "
                    f"(constants → facts → choices → definitions → constraints → "
                    f"optimization → show). Quick Fix: Fix Order."
                ),
                severity=DiagnosticSeverity.Information,
                source="aspls",
                code=CODE_RULE_ORDER,
            )
        )

    for c in constructs:
        if c.has_preceding_comment:
            continue
        line = c.start_line
        code_line = c.text.split("\n")
        # Prefer the first code line length for range end
        first = next((ln for ln in code_line if ln.strip() and not ln.lstrip().startswith("%")), code_line[0] if code_line else "")
        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=0),
                    end=Position(line=line, character=max(len(first), 1)),
                ),
                message=(
                    "Add a % comment above this statement to explain it. "
                    "Quick Fix: Add preceding comment."
                ),
                severity=DiagnosticSeverity.Information,
                source="aspls",
                code=CODE_MISSING_COMMENT,
            )
        )

    diagnostics.extend(build_learner_hints(text, tree))
    return diagnostics


def build_diagnostics(
    text: str,
    *,
    once_used: bool = True,
    learner_mode: bool = False,
    index: dict | None = None,
    document_uri: str | None = None,
) -> list[Diagnostic]:
    result = parse_document(text)
    diagnostics = []
    for error in result.errors:
        line = max(error.line - 1, 0)
        column = max(error.column - 1, 0)
        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=column),
                    end=Position(line=line, character=column + 1),
                ),
                message=error.message,
                severity=DiagnosticSeverity.Error,
                source="aspls",
            )
        )

    if not result.errors:
        for finding in find_unsafe_variables(result.tree):
            line = max(finding.line - 1, 0)
            column = max(finding.column - 1, 0)
            vars_list = ", ".join(finding.variables)
            msg = (
                f"Unsafe variable: {vars_list}"
                if len(finding.variables) == 1
                else f"Unsafe variables: {vars_list}"
            )
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line, character=column),
                        end=Position(line=line, character=column + 1),
                    ),
                    message=msg,
                    severity=DiagnosticSeverity.Error,
                    source="aspls",
                )
            )

        if once_used:
            symbol_index = index if index is not None else build_symbol_index(result.tree)
            for (name, arity), occurrences in symbol_index.items():
                non_dir = [o for o in occurrences if o.role not in DIRECTIVE_ROLES]
                if len(non_dir) != 1:
                    continue
                # #show / #minimize / #maximize counts as a use alongside the sole occurrence.
                if any(o.role in DIRECTIVE_ROLES for o in occurrences):
                    continue
                occ = non_dir[0]
                # Lone definition (fact / rule head) — suppress didactic false positives.
                if occ.role in DEFINING_ROLES:
                    continue
                occ_uri = getattr(occ, "uri", None)
                if (
                    document_uri is not None
                    and occ_uri is not None
                    and occ_uri != document_uri
                ):
                    continue
                line = max(occ.line - 1, 0)
                column = max(occ.column - 1, 0)
                if occ.role == "rule_body":
                    where = "in a rule body"
                elif occ.role == "constraint":
                    where = "in a constraint"
                elif occ.role == "weak":
                    where = "in a weak constraint"
                else:
                    where = "as a use"
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=column),
                            end=Position(line=line, character=column + len(occ.name)),
                        ),
                        message=(
                            f"Predicate {name}/{arity} appears only once {where} — "
                            f"check for a typo or add a definition"
                        ),
                        severity=DiagnosticSeverity.Warning,
                        source="aspls",
                    )
                )

        for clingo_diag in check_with_clingo(text):
            line = max(clingo_diag.line - 1, 0)
            column = max(clingo_diag.column - 1, 0)
            severity = (
                DiagnosticSeverity.Error
                if clingo_diag.severity == "error"
                else DiagnosticSeverity.Warning
            )
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line, character=column),
                        end=Position(line=line, character=column + 1),
                    ),
                    message=clingo_diag.message,
                    severity=severity,
                    source="aspls (clingo)",
                )
            )

    # Learner-mode warnings are source-based and still useful when some
    # statements fail to parse (order/comments apply to recoverable constructs).
    if learner_mode:
        diagnostics.extend(_learner_diagnostics(text, result.tree))

    return diagnostics
