from dataclasses import dataclass, field
from pathlib import Path

import lark
from lark import Lark, UnexpectedInput

GRAMMAR_PATH = Path(__file__).parent / "grammar" / "asp_core2.lark"

_parser = Lark(GRAMMAR_PATH.read_text(), parser="earley", propagate_positions=True)


@dataclass
class ParseError:
    line: int
    column: int
    message: str


@dataclass
class ParseResult:
    tree: lark.Tree | None
    errors: list[ParseError] = field(default_factory=list)


def parse_document(text: str) -> ParseResult:
    try:
        tree = _parser.parse(text)
        return ParseResult(tree=tree, errors=[])
    except UnexpectedInput as e:
        error = ParseError(line=e.line, column=e.column, message=str(e))
        return ParseResult(tree=None, errors=[error])
