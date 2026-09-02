"""Collect grounding steps via clingo's ground-program observer."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import clingo
except ImportError as exc:
    raise RuntimeError(
        "clingo Python module is required for grounding debug. "
        "Install clingo (pip install clingo or system package)."
    ) from exc


@dataclass(frozen=True)
class GroundingStep:
    kind: str
    detail: str


def _format_literals(ids: list[int], atoms: dict[int, str]) -> list[str]:
    out: list[str] = []
    for lit in ids:
        sign = "not " if lit < 0 else ""
        atom_id = abs(lit)
        symbol = atoms.get(atom_id, f"#{atom_id}")
        out.append(f"{sign}{symbol}")
    return out


class _StepCollector(clingo.backend.Observer):
    def __init__(self) -> None:
        self.steps: list[GroundingStep] = []
        self._atoms: dict[int, str] = {}

    def init_program(self, incremental: bool) -> None:
        self.steps.append(
            GroundingStep(
                kind="init_program",
                detail=f"incremental={incremental}",
            )
        )

    def begin_step(self) -> None:
        self.steps.append(GroundingStep(kind="begin_step", detail=""))

    def end_step(self) -> None:
        self.steps.append(GroundingStep(kind="end_step", detail=""))

    def output_atom(self, symbol: clingo.Symbol, atom: int) -> None:
        text = str(symbol)
        if atom:
            self._atoms[atom] = text
        self.steps.append(GroundingStep(kind="fact", detail=text))

    def rule(self, choice: bool, head: list[int], body: list[int]) -> None:
        head_text = ", ".join(self._atoms.get(a, f"#{a}") for a in head) or "∅"
        body_text = ", ".join(_format_literals(list(body), self._atoms)) or "∅"
        prefix = "choice rule" if choice else "rule"
        self.steps.append(
            GroundingStep(
                kind="rule",
                detail=f"{prefix}: {head_text} :- {body_text}",
            )
        )

    def minimize(self, priority: int, literals: list[tuple[int, int]]) -> None:
        parts = [
            f"{w}*{self._atoms.get(abs(lit), f'#{abs(lit)}')}"
            for lit, w in literals
        ]
        self.steps.append(
            GroundingStep(
                kind="minimize",
                detail=f"priority={priority}: {' + '.join(parts) or '∅'}",
            )
        )


def collect_grounding_steps(program_path: str | Path) -> list[GroundingStep]:
    path = Path(program_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Program file not found: {path}")

    collector = _StepCollector()
    ctl = clingo.Control()
    ctl.register_observer(collector)
    ctl.load(str(path))
    ctl.ground([("base", [])])
    return collector.steps


def steps_to_json(steps: list[GroundingStep]) -> list[dict[str, Any]]:
    return [asdict(step) for step in steps]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print(
            "Usage: python grounding_debug.py <program.lp>",
            file=sys.stderr,
        )
        return 2

    try:
        steps = collect_grounding_steps(args[0])
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "steps": []}))
        return 1

    print(json.dumps({"ok": True, "error": None, "steps": steps_to_json(steps)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
