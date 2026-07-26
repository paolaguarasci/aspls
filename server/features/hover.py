from lsprotocol.types import Hover, MarkupContent, MarkupKind

from parser import parse_document
from symbols import Occurrence, build_symbol_index


def _find_occurrence_at(
    index: dict[tuple[str, int], list[Occurrence]], line_1indexed: int, column_1indexed: int
) -> tuple[str, int] | None:
    for (name, arity), occurrences in index.items():
        for occ in occurrences:
            token_end_column = occ.column + len(occ.name)
            if occ.line == line_1indexed and occ.column <= column_1indexed < token_end_column:
                return (name, arity)
    return None


def build_hover(text: str, line: int, column: int) -> Hover | None:
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    key = _find_occurrence_at(index, line + 1, column + 1)
    if key is None:
        return None

    name, arity = key
    occurrences = index[key]
    head_count = sum(1 for occ in occurrences if occ.role == "head")
    body_count = sum(1 for occ in occurrences if occ.role == "body")

    text_value = f"**{name}/{arity}**\n\n{head_count} head occurrence(s), {body_count} body occurrence(s)"
    return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=text_value))
