from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from parser import parse_document
from clingo_check import check_with_clingo
from safety import find_unsafe_variables
from symbols import DIRECTIVE_ROLES, build_symbol_index


def build_diagnostics(
    text: str,
    *,
    once_used: bool = True,
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
                counted = [o for o in occurrences if o.role not in DIRECTIVE_ROLES]
                if len(counted) != 1:
                    continue
                occ = counted[0]
                occ_uri = getattr(occ, "uri", None)
                if (
                    document_uri is not None
                    and occ_uri is not None
                    and occ_uri != document_uri
                ):
                    continue
                line = max(occ.line - 1, 0)
                column = max(occ.column - 1, 0)
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=column),
                            end=Position(line=line, character=column + len(occ.name)),
                        ),
                        message=f"Predicate {name}/{arity} is used only once",
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

    return diagnostics
