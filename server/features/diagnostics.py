from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from parser import parse_document


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
    return diagnostics
