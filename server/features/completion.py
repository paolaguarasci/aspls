from lsprotocol.types import CompletionItem, CompletionItemKind, InsertTextFormat

from parser import parse_document
from symbols import build_symbol_index


def _snippet_insert_text(name: str, arity: int) -> tuple[str, InsertTextFormat | None]:
    if arity <= 0:
        return name, None
    args = ", ".join(f"${{{i}:X{i}}}" for i in range(1, arity + 1))
    return f"{name}({args})", InsertTextFormat.Snippet


def build_completions_from_index(index: dict) -> list[CompletionItem]:
    items = []
    for name, arity in index:
        insert_text, fmt = _snippet_insert_text(name, arity)
        item = CompletionItem(
            label=f"{name}/{arity}",
            kind=CompletionItemKind.Function,
            insert_text=insert_text,
        )
        if fmt is not None:
            item.insert_text_format = fmt
        items.append(item)
    return items


def build_completions(text: str) -> list[CompletionItem]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    return build_completions_from_index(index)
