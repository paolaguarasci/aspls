from pygls.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
)

from features.diagnostics import build_diagnostics

server = LanguageServer("aspls", "v0.1.0")


def _publish_diagnostics(uri: str, text: str) -> None:
    diagnostics = build_diagnostics(text)
    server.publish_diagnostics(uri, diagnostics)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    _publish_diagnostics(params.text_document.uri, params.text_document.text)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    _publish_diagnostics(params.text_document.uri, doc.source)


if __name__ == "__main__":
    server.start_io()
