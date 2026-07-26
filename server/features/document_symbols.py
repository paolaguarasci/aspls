from __future__ import annotations

from lsprotocol.types import DocumentSymbol

from parser import parse_document
from symbols import build_symbol_index
from features.predicate_tree import build_document_symbols_from_index


def build_document_symbols(text: str) -> list[DocumentSymbol]:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    return build_document_symbols_from_index(index)
