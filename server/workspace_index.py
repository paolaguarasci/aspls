from __future__ import annotations

from collections.abc import Callable
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


def resolve_entry_path(
    active_uri: str,
    entry: str,
    workspace_roots: list[str],
) -> str:
    """Resolve a relative or absolute path entry to a file URI.

    Resolution order (mirrors client resolveAdditionalFiles):
    active-file directory first, then workspace roots in order.
    """
    active_path = _uri_to_path(active_uri)
    if Path(entry).is_absolute():
        return _path_to_uri(Path(entry))
    candidate = (active_path.parent / entry).resolve()
    if not candidate.exists():
        for root in workspace_roots:
            alt = (Path(root) / entry).resolve()
            if alt.exists():
                candidate = alt
                break
    return _path_to_uri(candidate)


def extract_includes(text: str) -> list[str]:
    """Return #include paths from parsed source (without quotes)."""
    result = parse_document(text)
    if result.tree is None:
        return []
    paths: list[str] = []
    for statement_wrapper in result.tree.children:
        if not statement_wrapper.children:
            continue
        statement = statement_wrapper.children[0]
        if statement.data == "include_directive":
            raw = str(statement.children[0])
            paths.append(raw[1:-1])
    return paths


def expand_include_closure(
    seed_uris: list[str],
    workspace_roots: list[str],
    get_text: Callable[[str], str | None],
) -> set[str]:
    """Transitively collect URIs reachable via #include from seed files."""
    seen: set[str] = set()
    queue = list(seed_uris)
    while queue:
        uri = queue.pop()
        if uri in seen:
            continue
        seen.add(uri)
        text = get_text(uri)
        if text is None:
            continue
        for include_path in extract_includes(text):
            resolved = resolve_entry_path(uri, include_path, workspace_roots)
            if resolved not in seen:
                queue.append(resolved)
    return seen


def resolve_pool(
    active_uri: str,
    workspace_roots: list[str],
    config_path: str | None,
    additional_files: list[str] | None,
    discovered_uris: list[str],
    get_text: Callable[[str], str | None] | None = None,
) -> list[str]:
    """Compute the file pool for LSP features.

    Rules (canonical, must match client resolveAdditionalFiles logic):
    - additional_files is None  → full-workspace fallback: return discovered_uris.
    - additional_files == []    → explicit empty: pool is {active_uri} + #includes.
    - additional_files non-empty → pool is {active_uri} + resolved entries + #includes.
      Resolution order per entry: active-file directory first, then workspace
      roots in order (mirrors client resolveAdditionalFiles).

    When additional_files is not None and get_text is provided, #include targets
    reachable from the active file are unioned into the pool (transitive).
    """
    if additional_files is None:
        return list(discovered_uris)

    uris: set[str] = {active_uri}
    for entry in additional_files:
        uris.add(resolve_entry_path(active_uri, entry, workspace_roots))

    if get_text is not None:
        uris |= expand_include_closure([active_uri], workspace_roots, get_text)

    return sorted(uris)


class WorkspaceIndex:
    def __init__(self) -> None:
        self._docs: dict[str, dict[tuple[str, int], list[Occurrence]]] = {}
        self._merged_cache: dict[
            frozenset[str], dict[tuple[str, int], list[IndexedOccurrence]]
        ] = {}

    def upsert(self, uri: str, text: str) -> None:
        tree = parse_document(text).tree
        self._docs[uri] = build_symbol_index(tree)
        self._invalidate_cache_for({uri})

    def remove(self, uri: str) -> None:
        self._docs.pop(uri, None)
        self._invalidate_cache_for({uri})

    def has(self, uri: str) -> bool:
        return uri in self._docs

    def _invalidate_cache_for(self, uris: set[str]) -> None:
        for key in [k for k in self._merged_cache if k & uris]:
            del self._merged_cache[key]

    def _merge_uncached(
        self, keys: list[str]
    ) -> dict[tuple[str, int], list[IndexedOccurrence]]:
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

    def merged(self, uris: list[str] | None = None) -> dict[tuple[str, int], list[IndexedOccurrence]]:
        keys = uris if uris is not None else list(self._docs.keys())
        cache_key = frozenset(keys)
        cached = self._merged_cache.get(cache_key)
        if cached is not None:
            return cached
        merged = self._merge_uncached(keys)
        self._merged_cache[cache_key] = merged
        return merged
