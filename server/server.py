from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from pygls.server import LanguageServer
from lsprotocol.types import (
    INITIALIZED,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    WORKSPACE_SYMBOL,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_REFERENCES,
    TEXT_DOCUMENT_RENAME,
    TEXT_DOCUMENT_PREPARE_RENAME,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_SIGNATURE_HELP,
    TEXT_DOCUMENT_DOCUMENT_LINK,
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_FORMATTING,
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    TEXT_DOCUMENT_INLAY_HINT,
    TEXT_DOCUMENT_CODE_LENS,
    WORKSPACE_DID_CHANGE_CONFIGURATION,
    WORKSPACE_DID_CHANGE_WORKSPACE_FOLDERS,
    WORKSPACE_DID_CHANGE_WATCHED_FILES,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    DidChangeConfigurationParams,
    DidChangeWatchedFilesParams,
    DidChangeWorkspaceFoldersParams,
    HoverParams,
    DocumentSymbolParams,
    WorkspaceSymbolParams,
    DefinitionParams,
    ReferenceParams,
    RenameParams,
    PrepareRenameParams,
    CompletionParams,
    SignatureHelpParams,
    DocumentLinkParams,
    CodeActionParams,
    DocumentFormattingParams,
    SemanticTokensParams,
    SemanticTokensLegend,
    InlayHintParams,
    CodeLensParams,
    InitializedParams,
)

from features.diagnostics import build_diagnostics
from features.document_symbols import build_document_symbols
from features.hover import build_hover_from_index
from features.definition import build_definitions_from_index
from features.references import build_references_from_index
from features.rename import build_prepare_rename_from_index, build_rename_edit_from_index
from features.completion import build_completions_from_index
from features.signature_help import build_signature_help_from_index
from features.document_links import build_document_links
from features.code_actions import build_code_actions
from features.formatting import build_format_edits
from features.semantic_tokens import (
    TOKEN_MODIFIERS,
    TOKEN_TYPES,
    build_semantic_tokens,
)
from features.workspace_predicates import build_workspace_predicate_nodes
from features.workspace_symbols import build_workspace_symbols
from features.inlay_hints import build_inlay_hints
from features.code_lens import build_code_lenses_from_index
from workspace_index import WorkspaceIndex, resolve_pool

server = LanguageServer("aspls", "v0.1.0")

# Fallback when workspace/didChangeConfiguration has not yet arrived.
ONCE_USED = True
LEARNER_MODE = False

WORKSPACE = WorkspaceIndex()
DISCOVERED: list[str] = []
WORKSPACE_ROOTS: list[str] = []
ADDITIONAL_FILES: list[str] | None = None
CONFIG_FILE_NAME = "aspls.clingo.json"

_SKIP_DIRS = frozenset({"node_modules", ".git", ".venv", "out", "__pycache__"})
_ASP_SUFFIXES = frozenset({".lp", ".asp"})


def _uri_to_path(uri: str) -> Path:
    return Path(unquote(urlparse(uri).path))


def _path_to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def is_config_file_change(uri: str, config_file_name: str | None = None) -> bool:
    """True when the changed URI's basename matches the active config file name."""
    name = (config_file_name if config_file_name is not None else CONFIG_FILE_NAME).strip()
    if not name:
        name = "aspls.clingo.json"
    try:
        return _uri_to_path(uri).name == name
    except Exception:
        return False


def _extract_once_used(settings) -> bool | None:
    """Pull aspls.diagnostics.onceUsed from didChangeConfiguration settings."""
    if not isinstance(settings, dict):
        return None
    aspls = settings.get("aspls", settings)
    if not isinstance(aspls, dict):
        return None
    diagnostics = aspls.get("diagnostics")
    if isinstance(diagnostics, dict) and "onceUsed" in diagnostics:
        return bool(diagnostics["onceUsed"])
    if "diagnostics.onceUsed" in aspls:
        return bool(aspls["diagnostics.onceUsed"])
    return None


def _extract_config_file_name(settings) -> str | None:
    """Pull aspls.clingo.configFile from didChangeConfiguration settings."""
    if not isinstance(settings, dict):
        return None
    aspls = settings.get("aspls", settings)
    if not isinstance(aspls, dict):
        return None
    clingo = aspls.get("clingo")
    if isinstance(clingo, dict) and isinstance(clingo.get("configFile"), str):
        return clingo["configFile"]
    if "clingo.configFile" in aspls and isinstance(aspls["clingo.configFile"], str):
        return aspls["clingo.configFile"]
    return None


def _extract_learner_mode(settings) -> bool | None:
    """Pull aspls.learnerMode from didChangeConfiguration settings."""
    if not isinstance(settings, dict):
        return None
    aspls = settings.get("aspls", settings)
    if not isinstance(aspls, dict):
        return None
    if "learnerMode" in aspls:
        return bool(aspls["learnerMode"])
    return None


def _once_used_enabled() -> bool:
    return ONCE_USED


def _learner_mode_enabled() -> bool:
    return LEARNER_MODE


def _workspace_root_paths(ls: LanguageServer) -> list[str]:
    roots: list[str] = []
    try:
        for folder in ls.workspace.folders.values():
            roots.append(_uri_to_path(folder.uri).as_posix())
    except Exception:
        pass
    if not roots:
        try:
            root = ls.workspace.root_path
            if root:
                roots.append(str(root))
        except Exception:
            pass
    return roots


def _read_additional_files_from_config(roots: list[str]) -> list[str] | None:
    """Read additionalFiles from aspls.clingo.json.

    Returns:
    - list[str] (possibly empty) when the key is present and is a JSON array.
      An empty array [] is returned as [] so resolve_pool treats it as explicit
      "active file only", not as a fallback to full-workspace discovery.
    - None when the key is absent or the config file does not exist / is invalid.
    """
    name = CONFIG_FILE_NAME.strip() or "aspls.clingo.json"
    for root in roots:
        config_path = Path(root) / name
        if not config_path.is_file():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        files = data.get("additionalFiles")
        if isinstance(files, list):
            return [f for f in files if isinstance(f, str)]
    return None


def _discover_asp_files(roots: list[str]) -> list[str]:
    uris: list[str] = []
    for root in roots:
        root_path = Path(root)
        if not root_path.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for name in filenames:
                if Path(name).suffix.lower() in _ASP_SUFFIXES:
                    uris.append(_path_to_uri(Path(dirpath) / name))
    return sorted(set(uris))


def _load_file_text(uri: str) -> str | None:
    path = _uri_to_path(uri)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _ensure_indexed(uri: str) -> None:
    """Load on-disk content into the index when not already present from an open doc."""
    text = _load_file_text(uri)
    if text is not None:
        WORKSPACE.upsert(uri, text)


def _refresh_workspace_scan(ls: LanguageServer | None = None) -> None:
    global DISCOVERED, WORKSPACE_ROOTS, ADDITIONAL_FILES
    if ls is not None:
        WORKSPACE_ROOTS = _workspace_root_paths(ls)
    DISCOVERED = _discover_asp_files(WORKSPACE_ROOTS)
    # Always assign: None/empty config clears stale ADDITIONAL_FILES so
    # resolve_pool falls back to discovered-only.
    ADDITIONAL_FILES = _read_additional_files_from_config(WORKSPACE_ROOTS)
    open_uris: set[str] = set()
    if ls is not None:
        try:
            open_uris = set(ls.workspace.text_documents.keys())
        except Exception:
            pass
    for uri in DISCOVERED:
        if uri not in open_uris:
            _ensure_indexed(uri)


def _text_for_uri(uri: str) -> str | None:
    try:
        doc = server.workspace.get_text_document(uri)
        return doc.source
    except Exception:
        return _load_file_text(uri)


def _pool_for(uri: str) -> list[str]:
    pool = resolve_pool(
        active_uri=uri,
        workspace_roots=WORKSPACE_ROOTS,
        config_path=None,
        additional_files=ADDITIONAL_FILES,
        discovered_uris=DISCOVERED,
        get_text=_text_for_uri,
    )
    for pool_uri in pool:
        if not WORKSPACE.has(pool_uri):
            _ensure_indexed(pool_uri)
    return pool


def _merged_for(uri: str):
    return WORKSPACE.merged(_pool_for(uri))


def _document_index_for(uri: str):
    """Active-document index for cursor key resolution (URI-scoped)."""
    if not WORKSPACE.has(uri):
        _ensure_indexed(uri)
    return WORKSPACE.merged([uri])


def _publish_diagnostics(uri: str, text: str) -> None:
    WORKSPACE.upsert(uri, text)
    if uri not in DISCOVERED:
        DISCOVERED.append(uri)
    merged = _merged_for(uri)
    diagnostics = build_diagnostics(
        text,
        once_used=_once_used_enabled(),
        learner_mode=_learner_mode_enabled(),
        index=merged,
        document_uri=uri,
    )
    server.publish_diagnostics(uri, diagnostics)


def _republish_open_diagnostics(ls: LanguageServer) -> None:
    try:
        documents = ls.workspace.text_documents
    except RuntimeError:
        return
    for uri, doc in documents.items():
        _publish_diagnostics(uri, doc.source)


@server.feature(INITIALIZED)
def on_initialized(ls: LanguageServer, params: InitializedParams):
    _refresh_workspace_scan(ls)


@server.feature(WORKSPACE_DID_CHANGE_WORKSPACE_FOLDERS)
def did_change_workspace_folders(
    ls: LanguageServer, params: DidChangeWorkspaceFoldersParams
):
    _refresh_workspace_scan(ls)


@server.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
def did_change_configuration(ls: LanguageServer, params: DidChangeConfigurationParams):
    global ONCE_USED, LEARNER_MODE, CONFIG_FILE_NAME
    value = _extract_once_used(params.settings)
    if value is not None:
        ONCE_USED = value
    learner = _extract_learner_mode(params.settings)
    if learner is not None:
        LEARNER_MODE = learner
    config_name = _extract_config_file_name(params.settings)
    if config_name:
        CONFIG_FILE_NAME = config_name
    # Pool comes only from aspls.clingo.json additionalFiles (or full workspace).
    # Never drive ADDITIONAL_FILES from VS Code setting aspls.clingo.additionalFiles.
    _refresh_workspace_scan(ls)
    _republish_open_diagnostics(ls)


@server.feature(WORKSPACE_DID_CHANGE_WATCHED_FILES)
def did_change_watched_files(ls: LanguageServer, params: DidChangeWatchedFilesParams):
    relevant = any(is_config_file_change(change.uri) for change in params.changes)
    if not relevant:
        return
    _refresh_workspace_scan(ls)
    _republish_open_diagnostics(ls)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    if not WORKSPACE_ROOTS:
        _refresh_workspace_scan(ls)
    _publish_diagnostics(params.text_document.uri, params.text_document.text)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    _publish_diagnostics(params.text_document.uri, doc.source)


@server.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: HoverParams):
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    return build_hover_from_index(
        _merged_for(uri),
        params.position.line,
        params.position.character,
        uri,
        document_index=_document_index_for(uri),
        source=doc.source,
    )


@server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: LanguageServer, params: DocumentSymbolParams):
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    return build_document_symbols(doc.source)


@server.feature(WORKSPACE_SYMBOL)
def workspace_symbol(ls: LanguageServer, params: WorkspaceSymbolParams):
    _refresh_workspace_scan(ls)
    for uri in DISCOVERED:
        if not WORKSPACE.has(uri):
            _ensure_indexed(uri)
    merged = WORKSPACE.merged(DISCOVERED)
    return build_workspace_symbols(merged, params.query)


@server.feature("aspls/workspacePredicates")
def workspace_predicates(ls: LanguageServer, params):
    """Custom request: nested predicates for pool-or-discovered files.

    params: {"uri": str | None}
    """
    _refresh_workspace_scan(ls)
    uri = None
    if isinstance(params, dict):
        uri = params.get("uri")
    else:
        uri = getattr(params, "uri", None)
    if uri:
        pool = _pool_for(uri)
    else:
        pool = list(DISCOVERED)
        for pool_uri in pool:
            if not WORKSPACE.has(pool_uri):
                _ensure_indexed(pool_uri)
    merged = WORKSPACE.merged(pool)
    return build_workspace_predicate_nodes(merged, WORKSPACE_ROOTS)


@server.feature(TEXT_DOCUMENT_DEFINITION)
def definition(ls: LanguageServer, params: DefinitionParams):
    uri = params.text_document.uri
    return build_definitions_from_index(
        _merged_for(uri),
        params.position.line,
        params.position.character,
        uri,
        document_index=_document_index_for(uri),
    )


@server.feature(TEXT_DOCUMENT_REFERENCES)
def references(ls: LanguageServer, params: ReferenceParams):
    uri = params.text_document.uri
    return build_references_from_index(
        _merged_for(uri),
        params.position.line,
        params.position.character,
        uri,
        document_index=_document_index_for(uri),
    )


@server.feature(TEXT_DOCUMENT_PREPARE_RENAME)
def prepare_rename(ls: LanguageServer, params: PrepareRenameParams):
    uri = params.text_document.uri
    return build_prepare_rename_from_index(
        _merged_for(uri),
        params.position.line,
        params.position.character,
        uri,
        document_index=_document_index_for(uri),
    )


@server.feature(TEXT_DOCUMENT_RENAME)
def rename(ls: LanguageServer, params: RenameParams):
    uri = params.text_document.uri
    return build_rename_edit_from_index(
        _merged_for(uri),
        params.position.line,
        params.position.character,
        params.new_name,
        uri,
        document_index=_document_index_for(uri),
    )


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    uri = params.text_document.uri
    return build_completions_from_index(_merged_for(uri))


@server.feature(TEXT_DOCUMENT_SIGNATURE_HELP)
def signature_help(ls: LanguageServer, params: SignatureHelpParams):
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    return build_signature_help_from_index(
        _merged_for(uri),
        params.position.line,
        params.position.character,
        uri,
        document_index=_document_index_for(uri),
        source=doc.source,
    )


@server.feature(TEXT_DOCUMENT_DOCUMENT_LINK)
def document_link(ls: LanguageServer, params: DocumentLinkParams):
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    return build_document_links(doc.source, uri, WORKSPACE_ROOTS)


@server.feature(TEXT_DOCUMENT_FORMATTING)
def formatting(ls: LanguageServer, params: DocumentFormattingParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    edits = build_format_edits(doc.source)
    return edits if edits else []


@server.feature(TEXT_DOCUMENT_CODE_ACTION)
def code_action(ls: LanguageServer, params: CodeActionParams):
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    return build_code_actions(
        uri,
        doc.source,
        learner_mode=_learner_mode_enabled(),
        diagnostics=list(params.context.diagnostics)
        if params.context and params.context.diagnostics
        else None,
    )


@server.feature(
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    SemanticTokensLegend(token_types=TOKEN_TYPES, token_modifiers=TOKEN_MODIFIERS),
)
def semantic_tokens_full(ls: LanguageServer, params: SemanticTokensParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return build_semantic_tokens(doc.source)


@server.feature(TEXT_DOCUMENT_INLAY_HINT)
def inlay_hint(ls: LanguageServer, params: InlayHintParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return build_inlay_hints(doc.source, params.range)


@server.feature(TEXT_DOCUMENT_CODE_LENS)
def code_lens(ls: LanguageServer, params: CodeLensParams):
    uri = params.text_document.uri
    return build_code_lenses_from_index(uri, _merged_for(uri))


if __name__ == "__main__":
    server.start_io()
