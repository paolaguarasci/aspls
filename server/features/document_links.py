from lsprotocol.types import DocumentLink, Position, Range

from parser import parse_document
from workspace_index import resolve_entry_path


def build_document_links(
    text: str,
    uri: str,
    workspace_roots: list[str],
) -> list[DocumentLink]:
    """Return clickable links for #include \"path\" directives."""
    result = parse_document(text)
    if result.tree is None:
        return []

    links: list[DocumentLink] = []
    for statement_wrapper in result.tree.children:
        if not statement_wrapper.children:
            continue
        statement = statement_wrapper.children[0]
        if statement.data != "include_directive":
            continue
        token = statement.children[0]
        raw = str(token)
        include_path = raw[1:-1]
        target = resolve_entry_path(uri, include_path, workspace_roots)
        start = Position(line=token.line - 1, character=token.column)
        end = Position(line=token.end_line - 1, character=token.end_column - 2)
        links.append(
            DocumentLink(
                range=Range(start=start, end=end),
                target=target,
            )
        )
    return links
