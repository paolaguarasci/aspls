from pygls.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_REFERENCES,
    TEXT_DOCUMENT_COMPLETION,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    HoverParams,
    DefinitionParams,
    ReferenceParams,
    CompletionParams,
)

from features.diagnostics import build_diagnostics
from features.hover import build_hover
from features.definition import build_definitions
from features.references import build_references
from features.completion import build_completions

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


@server.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: HoverParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return build_hover(doc.source, params.position.line, params.position.character)


@server.feature(TEXT_DOCUMENT_DEFINITION)
def definition(ls: LanguageServer, params: DefinitionParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return build_definitions(
        doc.source, params.position.line, params.position.character, params.text_document.uri
    )


@server.feature(TEXT_DOCUMENT_REFERENCES)
def references(ls: LanguageServer, params: ReferenceParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return build_references(
        doc.source, params.position.line, params.position.character, params.text_document.uri
    )


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return build_completions(doc.source)


if __name__ == "__main__":
    server.start_io()
