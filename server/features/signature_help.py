from lsprotocol.types import (
    MarkupContent,
    MarkupKind,
    ParameterInformation,
    SignatureHelp,
    SignatureInformation,
)

from comments import line_at
from docstrings import extract_docstrings, find_param_at_column
from parser import parse_document
from symbols import build_symbol_index, find_key_covering


def _synthesized_signature(name: str, arity: int) -> tuple[str, list[str]]:
    if arity <= 0:
        return f"{name}.", []
    param_names = [f"X{i}" for i in range(1, arity + 1)]
    return f"{name}({', '.join(param_names)}).", param_names


def build_signature_help_from_index(
    index: dict,
    line: int,
    column: int,
    uri: str | None = None,
    *,
    document_index: dict | None = None,
    source: str | None = None,
) -> SignatureHelp | None:
    resolve_index = document_index if document_index is not None else index
    resolve_uri = None if document_index is not None else uri
    covered = find_key_covering(
        resolve_index, line + 1, column + 1, source=source, uri=resolve_uri
    )
    if covered is None:
        return None

    key, atom_occ = covered
    name, arity = key

    doc = extract_docstrings(source).get(key) if source is not None else None

    if doc is not None:
        label = doc.signature
        description = doc.description or None
        param_infos = [
            ParameterInformation(
                label=p.name,
                documentation=MarkupContent(
                    kind=MarkupKind.Markdown, value=p.description
                ),
            )
            for p in doc.parameters
        ]
    else:
        label, param_names = _synthesized_signature(name, arity)
        description = None
        param_infos = [
            ParameterInformation(label=pname) for pname in param_names
        ]

    active_parameter: int | None = None
    if source is not None and arity > 0 and column + 1 > atom_occ.column + len(name):
        atom_line = line_at(source, line + 1)
        active_parameter = find_param_at_column(
            atom_line, atom_occ.column, column + 1, arity
        )

    documentation = None
    if description:
        documentation = MarkupContent(kind=MarkupKind.Markdown, value=description)

    signature = SignatureInformation(
        label=label,
        documentation=documentation,
        parameters=param_infos,
    )
    return SignatureHelp(
        signatures=[signature],
        active_signature=0,
        active_parameter=active_parameter,
    )


def build_signature_help(text: str, line: int, column: int) -> SignatureHelp | None:
    result = parse_document(text)
    index = build_symbol_index(result.tree)
    return build_signature_help_from_index(
        index, line, column, document_index=index, source=text
    )
