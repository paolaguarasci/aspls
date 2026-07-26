from lsprotocol.types import CompletionItem, CompletionItemKind

from parser import parse_document
from symbols import build_symbol_index


def build_completions(text: str) -> list[CompletionItem]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)

    items = []
    for name, arity in index:
        insert_text = f"{name}(" if arity > 0 else name
        items.append(
            CompletionItem(
                label=f"{name}/{arity}",
                kind=CompletionItemKind.Function,
                insert_text=insert_text,
            )
        )
    return items
