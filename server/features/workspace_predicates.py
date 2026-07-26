from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from symbols import DEFINING_ROLES
from workspace_index import IndexedOccurrence
from features.predicate_tree import ROLE_ORDER


def _uri_to_path(uri: str) -> Path:
    return Path(unquote(urlparse(uri).path))


def _display_path(uri: str, workspace_roots: list[str]) -> str:
    path = _uri_to_path(uri)
    for root in workspace_roots:
        try:
            return str(path.resolve().relative_to(Path(root).resolve()))
        except ValueError:
            continue
    return str(path)


def _occ_label(uri: str, line: int, negated: bool, workspace_roots: list[str]) -> str:
    base = f"{_display_path(uri, workspace_roots)}:{line}"
    return f"not {base}" if negated else base


def _range_dict(line: int, column: int, name: str) -> dict:
    return {
        "start": {"line": line - 1, "character": column - 1},
        "end": {"line": line - 1, "character": column - 1 + len(name)},
    }


def build_workspace_predicate_nodes(
    merged: dict[tuple[str, int], list[IndexedOccurrence]],
    workspace_roots: list[str],
) -> list[dict]:
    out: list[dict] = []
    for (name, arity), occurrences in sorted(merged.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        roles_present = {o.role for o in occurrences}
        pick = next((o for o in occurrences if o.role in DEFINING_ROLES), occurrences[0])
        role_children: list[dict] = []
        for role in ROLE_ORDER:
            group = [o for o in occurrences if o.role == role]
            if not group:
                continue
            occ_children = [
                {
                    "name": _occ_label(o.uri, o.line, o.negated, workspace_roots),
                    "kind": "occurrence",
                    "uri": o.uri,
                    "range": _range_dict(o.line, o.column, o.name),
                    "negated": o.negated,
                    "children": [],
                }
                for o in group
            ]
            role_children.append(
                {
                    "name": role,
                    "kind": "role",
                    "detail": f"{len(group)} occ",
                    "uri": group[0].uri,
                    "range": _range_dict(group[0].line, group[0].column, group[0].name),
                    "children": occ_children,
                }
            )
        out.append(
            {
                "name": f"{name}/{arity}",
                "kind": "predicate",
                "detail": f"{', '.join(sorted(roles_present))} · {len(occurrences)} occ",
                "uri": pick.uri,
                "range": _range_dict(pick.line, pick.column, pick.name),
                "children": role_children,
            }
        )
    return out
