from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from parser import parse_document
from symbols import Occurrence, build_symbol_index


@dataclass
class IndexedOccurrence:
    name: str
    arity: int
    line: int
    column: int
    role: str
    uri: str
    negated: bool = False


def _uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    return Path(unquote(parsed.path))


def _path_to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def resolve_pool(
    active_uri: str,
    workspace_roots: list[str],
    config_path: str | None,
    additional_files: list[str] | None,
    discovered_uris: list[str],
) -> list[str]:
    if additional_files:
        active_path = _uri_to_path(active_uri)
        uris = {active_uri}
        for entry in additional_files:
            candidate = (active_path.parent / entry).resolve()
            if not candidate.exists():
                for root in workspace_roots:
                    alt = (Path(root) / entry).resolve()
                    if alt.exists():
                        candidate = alt
                        break
            uris.add(_path_to_uri(candidate))
        return sorted(uris)
    return list(discovered_uris)


class WorkspaceIndex:
    def __init__(self) -> None:
        self._docs: dict[str, dict[tuple[str, int], list[Occurrence]]] = {}

    def upsert(self, uri: str, text: str) -> None:
        tree = parse_document(text).tree
        self._docs[uri] = build_symbol_index(tree)

    def remove(self, uri: str) -> None:
        self._docs.pop(uri, None)

    def has(self, uri: str) -> bool:
        return uri in self._docs

    def merged(self, uris: list[str] | None = None) -> dict[tuple[str, int], list[IndexedOccurrence]]:
        keys = uris if uris is not None else list(self._docs.keys())
        out: dict[tuple[str, int], list[IndexedOccurrence]] = {}
        for uri in keys:
            index = self._docs.get(uri)
            if not index:
                continue
            for key, occurrences in index.items():
                bucket = out.setdefault(key, [])
                for occ in occurrences:
                    bucket.append(
                        IndexedOccurrence(
                            name=occ.name,
                            arity=occ.arity,
                            line=occ.line,
                            column=occ.column,
                            role=occ.role,
                            uri=uri,
                            negated=occ.negated,
                        )
                    )
        return out
