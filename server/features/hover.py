from lsprotocol.types import Hover, MarkupContent, MarkupKind

from comments import extract_preceding_comment, line_at
from docstrings import (
    extract_docstrings,
    find_param_at_column,
    format_docstring_markdown,
)
from parser import parse_document
from symbols import (
    DEFINING_ROLES,
    USING_ROLES,
    build_symbol_index,
    find_key_covering,
)


def _local_definition(occurrences, *, uri: str | None = None):
    """First defining occurrence in the active document (never a foreign URI)."""
    defining = []
    for occ in occurrences:
        if occ.role not in DEFINING_ROLES:
            continue
        occ_uri = getattr(occ, "uri", None)
        if uri is not None and occ_uri is not None and occ_uri != uri:
            continue
        defining.append(occ)
    return defining[0] if defining else None


def build_hover_from_index(
    index: dict,
    line: int,
    column: int,
    uri: str | None = None,
    *,
    document_index: dict | None = None,
    source: str | None = None,
) -> Hover | None:
    """Resolve cursor key from the active document, then count in ``index``.

    When ``source`` is provided, enrich with asp-lsp docstrings or EZASP-style
    definition line + preceding comment.
    """
    resolve_index = document_index if document_index is not None else index
    resolve_uri = None if document_index is not None else uri
    covered = find_key_covering(
        resolve_index, line + 1, column + 1, source=source, uri=resolve_uri
    )
    if covered is None:
        return None

    key, atom_occ = covered
    name, arity = key
    occurrences = index.get(key, [])
    head_count = sum(1 for occ in occurrences if occ.role in DEFINING_ROLES)
    body_count = sum(1 for occ in occurrences if occ.role in USING_ROLES)

    parts = [
        f"**{name}/{arity}**",
        "",
        f"{head_count} head occurrence(s), {body_count} body occurrence(s)",
    ]

    if source is not None:
        docs = extract_docstrings(source)
        doc = docs.get(key)

        # Param-specific hover when cursor is past the predicate name
        if (
            doc is not None
            and doc.parameters
            and column + 1 > atom_occ.column + len(atom_occ.name)
        ):
            atom_line = line_at(source, line + 1)
            idx = find_param_at_column(
                atom_line, atom_occ.column, column + 1, arity
            )
            if idx is not None and idx < len(doc.parameters):
                param = doc.parameters[idx]
                text_value = (
                    f"**{name}/{arity}** — `{param.name}`\n\n{param.description}"
                )
                return Hover(
                    contents=MarkupContent(kind=MarkupKind.Markdown, value=text_value)
                )

        if doc is not None:
            parts.append("")
            parts.append(format_docstring_markdown(doc))
        else:
            # Only read definition lines from the active document — never apply
            # another file's line number to the current buffer.
            local_occs = (
                document_index.get(key, [])
                if document_index is not None
                else occurrences
            )
            defining = _local_definition(local_occs, uri=uri)
            if defining is not None:
                def_line = line_at(source, defining.line)
                # Sanity: the line must mention this predicate name
                if def_line.strip() and name in def_line:
                    parts.append("")
                    parts.append("**Definition**")
                    parts.append(f"```asp\n{def_line.strip()}\n```")
                    preceding = extract_preceding_comment(source, defining.line)
                    if preceding is not None and preceding.text:
                        parts.append("")
                        parts.append("**Comment**")
                        parts.append(preceding.text)

    text_value = "\n".join(parts)
    return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=text_value))


def build_hover(text: str, line: int, column: int) -> Hover | None:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    return build_hover_from_index(
        index, line, column, document_index=index, source=text
    )
