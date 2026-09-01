import re

from lsprotocol.types import Position, Range, TextEdit, WorkspaceEdit

from symbols import find_key_at

_VALID_IDENTIFIER = re.compile(r"^[a-z][a-zA-Z0-9_]*$")


def _occurrence_range(occ) -> Range:
    start = Position(line=occ.line - 1, character=occ.column - 1)
    end = Position(line=occ.line - 1, character=occ.column - 1 + len(occ.name))
    return Range(start=start, end=end)


def build_prepare_rename_from_index(
    index: dict,
    line: int,
    column: int,
    uri: str | None = None,
    *,
    document_index: dict | None = None,
) -> Range | None:
    """Return the range of the predicate name under the cursor."""
    resolve_index = document_index if document_index is not None else index
    resolve_uri = None if document_index is not None else uri
    key = find_key_at(resolve_index, line + 1, column + 1, resolve_uri)
    if key is None:
        return None

    for occ in resolve_index.get(key, []):
        if resolve_uri is not None:
            occ_uri = getattr(occ, "uri", None)
            if occ_uri is not None and occ_uri != resolve_uri:
                continue
        token_end = occ.column + len(occ.name)
        if occ.line == line + 1 and occ.column <= column + 1 < token_end:
            return _occurrence_range(occ)
    return None


def build_rename_edit_from_index(
    index: dict,
    line: int,
    column: int,
    new_name: str,
    uri: str | None = None,
    *,
    document_index: dict | None = None,
) -> WorkspaceEdit | None:
    """Build a workspace edit renaming every occurrence of the predicate in ``index``."""
    if not _VALID_IDENTIFIER.match(new_name):
        return None

    resolve_index = document_index if document_index is not None else index
    resolve_uri = None if document_index is not None else uri
    key = find_key_at(resolve_index, line + 1, column + 1, resolve_uri)
    if key is None:
        return None

    if new_name == key[0]:
        return WorkspaceEdit(changes={})

    changes: dict[str, list[TextEdit]] = {}
    for occ in index.get(key, []):
        occ_uri = getattr(occ, "uri", None) or uri
        if occ_uri is None:
            continue
        changes.setdefault(occ_uri, []).append(
            TextEdit(range=_occurrence_range(occ), new_text=new_name)
        )

    if not changes:
        return None
    return WorkspaceEdit(changes=changes)
