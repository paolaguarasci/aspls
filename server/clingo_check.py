"""Optional Clingo-backed diagnostics.

Uses the Python ``clingo`` module when importable; otherwise falls back to the
``clingo`` binary on PATH. If neither is available, returns no findings so the
language server still works.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import clingo

    _CLINGO_MODULE = True
except ImportError:
    # clingo is an optional enhancement, not a required dependency: degrade to
    # a no-op instead of failing fast so the language server works without it.
    _CLINGO_MODULE = False


@dataclass
class ClingoDiagnostic:
    line: int
    column: int
    message: str
    severity: str = "warning"  # "error" | "warning"


_CLINGO_MSG_RE = re.compile(
    r"^.*?:(\d+):(\d+)(?:-\d+)?:\s*(error|info|warning):\s*(.*)$",
    re.IGNORECASE,
)


def _parse_clingo_messages(text: str) -> list[ClingoDiagnostic]:
    diagnostics: list[ClingoDiagnostic] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _CLINGO_MSG_RE.match(line)
        if not match:
            continue
        lineno = int(match.group(1))
        column = int(match.group(2))
        kind = match.group(3).lower()
        message = match.group(4).strip()
        severity = "error" if kind == "error" else "warning"
        diagnostics.append(
            ClingoDiagnostic(
                line=lineno,
                column=column,
                message=message,
                severity=severity,
            )
        )
    return diagnostics


def _check_with_module(text: str) -> list[ClingoDiagnostic]:
    diagnostics: list[ClingoDiagnostic] = []

    def _logger(_code: int, message: str) -> None:
        parsed = _parse_clingo_messages(message)
        if parsed:
            diagnostics.extend(parsed)
        else:
            diagnostics.append(
                ClingoDiagnostic(line=1, column=1, message=message, severity="warning")
            )

    ctl = clingo.Control(logger=_logger)
    try:
        ctl.add("base", [], text)
        ctl.ground([("base", [])])
    except RuntimeError as e:
        parsed = _parse_clingo_messages(str(e))
        if parsed:
            diagnostics.extend(parsed)
        else:
            diagnostics.append(
                ClingoDiagnostic(line=1, column=1, message=str(e), severity="error")
            )

    return diagnostics


def _check_with_cli(text: str) -> list[ClingoDiagnostic]:
    binary = shutil.which("clingo")
    if not binary:
        return []

    with tempfile.TemporaryDirectory(prefix="aspls-clingo-") as tmp:
        path = Path(tmp) / "check.lp"
        path.write_text(text, encoding="utf8")
        try:
            proc = subprocess.run(
                [binary, str(path), "1"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []

        combined = f"{proc.stdout}\n{proc.stderr}"
        diagnostics = _parse_clingo_messages(combined)
        if diagnostics:
            return diagnostics

        # Parsing/grounding failures sometimes only print a summary line.
        if "parsing failed" in combined.lower() or "grounding stopped" in combined.lower():
            return [
                ClingoDiagnostic(
                    line=1,
                    column=1,
                    message=combined.strip().splitlines()[-1]
                    if combined.strip()
                    else "Clingo failed",
                    severity="error",
                )
            ]
        return []


def check_with_clingo(text: str) -> list[ClingoDiagnostic]:
    if _CLINGO_MODULE:
        findings = _check_with_module(text)
    else:
        findings = _check_with_cli(text)
    # Surface real failures; skip noisy "info: atom does not occur…" notes.
    return [d for d in findings if d.severity == "error"]
