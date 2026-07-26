"""Parse asp-lsp-style ``%* ... *%`` predicate docstrings from source text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_SIGNATURE_RE = re.compile(
    r"^#\s*(?P<name>[a-z][a-zA-Z0-9_]*)\s*"
    r"(?:\((?P<params>[^)]*)\))?\s*\.?\s*$"
)
_PARAM_BULLET_RE = re.compile(
    r"^[-*]\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<desc>.+)\s*$"
)
_BLOCK_RE = re.compile(r"%\*(.*?)\*%", re.DOTALL)


@dataclass
class ParamDoc:
    name: str
    description: str


@dataclass
class PredicateDocstring:
    name: str
    arity: int
    signature: str
    description: str
    parameters: list[ParamDoc] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, int]:
        return self.name, self.arity


def _parse_signature_line(line: str) -> tuple[str, int, str, list[str]] | None:
    """Return (name, arity, signature_display, param_names) or None."""
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    # Allow ``#example_predicate(A,B,C).`` without requiring a space after #
    m = _SIGNATURE_RE.match(stripped)
    if not m:
        return None
    name = m.group("name")
    params_raw = m.group("params")
    if params_raw is None or params_raw.strip() == "":
        param_names: list[str] = []
    else:
        param_names = [p.strip() for p in params_raw.split(",") if p.strip()]
    arity = len(param_names)
    if arity == 0:
        signature = f"{name}."
    else:
        signature = f"{name}({', '.join(param_names)})."
    return name, arity, signature, param_names


def _parse_block(body: str) -> PredicateDocstring | None:
    lines = [ln.rstrip() for ln in body.strip("\n").split("\n")]
    # Drop empty leading/trailing
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return None

    sig = _parse_signature_line(lines[0].strip())
    if sig is None:
        return None
    name, arity, signature, param_names = sig

    rest = lines[1:]
    # Split description vs parameters section
    param_start = None
    for i, ln in enumerate(rest):
        low = ln.strip().lower()
        if low in ("#parameters", "parameters", "## parameters", "# parameters"):
            param_start = i
            break
        if low.startswith("#parameters"):
            param_start = i
            break

    if param_start is None:
        description = "\n".join(rest).strip()
        param_lines: list[str] = []
    else:
        description = "\n".join(rest[:param_start]).strip()
        param_lines = rest[param_start + 1 :]

    parameters: list[ParamDoc] = []
    for ln in param_lines:
        stripped = ln.strip()
        if not stripped:
            continue
        m = _PARAM_BULLET_RE.match(stripped)
        if m:
            parameters.append(
                ParamDoc(name=m.group("name"), description=m.group("desc").strip())
            )

    # If no bullet params but signature had names, leave parameters empty
    # (hover still shows signature + description).
    _ = param_names
    return PredicateDocstring(
        name=name,
        arity=arity,
        signature=signature,
        description=description,
        parameters=parameters,
    )


def extract_docstrings(text: str) -> dict[tuple[str, int], PredicateDocstring]:
    """Index docstrings by ``(name, arity)``. Later blocks override earlier ones."""
    result: dict[tuple[str, int], PredicateDocstring] = {}
    for match in _BLOCK_RE.finditer(text):
        doc = _parse_block(match.group(1))
        if doc is not None:
            result[doc.key] = doc
    return result


def format_docstring_markdown(doc: PredicateDocstring) -> str:
    parts = [f"`{doc.signature}`"]
    if doc.description:
        parts.append("")
        parts.append(doc.description)
    if doc.parameters:
        parts.append("")
        parts.append("**Parameters**")
        for p in doc.parameters:
            parts.append(f"- `{p.name}`: {p.description}")
    return "\n".join(parts)


def find_param_at_column(
    atom_line: str, atom_column_1based: int, cursor_column_1based: int, arity: int
) -> int | None:
    """Best-effort: which 0-based argument index the cursor is on inside ``name(...)``.

    ``atom_column_1based`` is the start of the predicate name on the line.
    Returns None if cursor is on the name or arity is 0 / unparseable.
    """
    if arity <= 0:
        return None
    # Find opening paren after atom name start
    start = atom_column_1based - 1
    if start < 0 or start >= len(atom_line):
        return None
    open_paren = atom_line.find("(", start)
    close_paren = atom_line.find(")", open_paren + 1) if open_paren >= 0 else -1
    if open_paren < 0 or close_paren < 0:
        return None
    cursor = cursor_column_1based - 1
    if cursor <= open_paren or cursor >= close_paren:
        return None
    inside = atom_line[open_paren + 1 : close_paren]
    # Split on top-level commas (no nesting for terms we care about)
    depth = 0
    parts: list[tuple[int, int]] = []
    part_start = 0
    for i, ch in enumerate(inside):
        if ch in "({":
            depth += 1
        elif ch in ")}":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append((part_start, i))
            part_start = i + 1
    parts.append((part_start, len(inside)))
    rel = cursor - (open_paren + 1)
    for idx, (a, b) in enumerate(parts):
        if a <= rel < b or (idx == len(parts) - 1 and a <= rel <= b):
            return idx if idx < arity else None
    return None
