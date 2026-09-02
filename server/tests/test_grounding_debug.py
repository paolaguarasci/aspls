import json
import subprocess
import sys
from pathlib import Path

import pytest

from grounding_debug import collect_grounding_steps, steps_to_json

ROOT = Path(__file__).resolve().parents[1]


def test_collect_grounding_steps_facts_and_rules(tmp_path: Path):
    program = tmp_path / "prog.lp"
    program.write_text("a(1). p(X) :- a(X).\n", encoding="utf-8")

    steps = collect_grounding_steps(program)
    kinds = [s.kind for s in steps]
    assert "init_program" in kinds
    assert "fact" in kinds
    assert "rule" in kinds
    assert any(s.detail == "a(1)" for s in steps if s.kind == "fact")
    assert any("p(1)" in s.detail for s in steps if s.kind == "fact")
    assert any(s.detail.startswith("rule:") for s in steps if s.kind == "rule")


def test_collect_grounding_steps_missing_file():
    with pytest.raises(FileNotFoundError):
        collect_grounding_steps("/no/such/file.lp")


def test_steps_to_json_roundtrip():
    steps = collect_grounding_steps(ROOT.parent / "examples" / "01_basics" / "birds.lp")
    payload = steps_to_json(steps)
    assert payload
    assert all("kind" in item and "detail" in item for item in payload)


def test_cli_json_output(tmp_path: Path):
    program = tmp_path / "one.lp"
    program.write_text("q.", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "grounding_debug.py"), str(program)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert any(s["kind"] == "fact" for s in data["steps"])
