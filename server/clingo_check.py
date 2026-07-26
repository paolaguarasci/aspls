from dataclasses import dataclass

try:
    import clingo

    _CLINGO_AVAILABLE = True
except ImportError:
    # clingo is an optional enhancement, not a required dependency: degrade to
    # a no-op instead of failing fast so the language server works without it.
    _CLINGO_AVAILABLE = False


@dataclass
class ClingoDiagnostic:
    line: int
    column: int
    message: str


def check_with_clingo(text: str) -> list[ClingoDiagnostic]:
    if not _CLINGO_AVAILABLE:
        return []

    diagnostics: list[ClingoDiagnostic] = []

    def _logger(code, message):
        diagnostics.append(ClingoDiagnostic(line=1, column=1, message=message))

    ctl = clingo.Control(logger=_logger)
    try:
        ctl.add("base", [], text)
        ctl.ground([("base", [])])
    except RuntimeError as e:
        diagnostics.append(ClingoDiagnostic(line=1, column=1, message=str(e)))

    return diagnostics
