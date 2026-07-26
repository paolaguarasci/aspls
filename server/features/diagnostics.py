from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from parser import parse_document
from clingo_check import check_with_clingo


def build_diagnostics(text: str) -> list[Diagnostic]:
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

    # Clingo only after a clean Lark parse: otherwise cascading parse noise.
    # The grammar tracks Clingo syntax; Clingo still catches grounding/safety.
    if not result.errors:
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
