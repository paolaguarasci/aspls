from dataclasses import dataclass

import lark

DEFINING_ROLES = frozenset({"fact", "rule_head"})
USING_ROLES = frozenset({"rule_body", "constraint", "minimize", "weak", "external"})
DIRECTIVE_ROLES = frozenset({"show", "minimize"})


@dataclass
class Occurrence:
    name: str
    arity: int
    line: int
    column: int
    role: str
    negated: bool = False


def _atom_name_and_arity(atom_node: lark.Tree) -> tuple[str, int]:
    if atom_node.data == "compound_atom":
        name = str(atom_node.children[0])
        arity = len(atom_node.children) - 1
        return name, arity
    # nullary_atom
    name = str(atom_node.children[0])
    return name, 0


def _collect_atoms_with_role(
    node, role: str, out: list[Occurrence], *, negated: bool = False
) -> None:
    if isinstance(node, lark.Tree):
        if node.data in ("compound_atom", "nullary_atom"):
            name, arity = _atom_name_and_arity(node)
            out.append(
                Occurrence(
                    name=name,
                    arity=arity,
                    line=node.meta.line,
                    column=node.meta.column,
                    role=role,
                    negated=negated,
                )
            )
            return
        if node.data == "negated_literal":
            for child in node.children:
                _collect_atoms_with_role(child, role, out, negated=True)
            return
        for child in node.children:
            _collect_atoms_with_role(child, role, out, negated=negated)


def find_key_at(
    index: dict, line: int, column: int, uri: str | None = None
) -> tuple[str, int] | None:
    """Return (name, arity) at line/column.

    When ``uri`` is set, only occurrences from that document match. This avoids
    cross-file collisions in a merged index where the same (line, column) can
    belong to different predicates in different files.
    """
    for (name, arity), occurrences in index.items():
        for occ in occurrences:
            if uri is not None:
                occ_uri = getattr(occ, "uri", None)
                if occ_uri is not None and occ_uri != uri:
                    continue
            token_end_column = occ.column + len(occ.name)
            if occ.line == line and occ.column <= column < token_end_column:
                return (name, arity)
    return None


def find_key_covering(
    index: dict,
    line: int,
    column: int,
    source: str | None = None,
    uri: str | None = None,
) -> tuple[tuple[str, int], "Occurrence"] | None:
    """Return ``((name, arity), occurrence)`` for the atom covering ``column``.

    Matches the predicate name token, or — when ``source`` is given — any
    column inside ``name(...)`` on that line (for parameter hover).
    """
    hit = find_key_at(index, line, column, uri)
    if hit is not None:
        for occ in index.get(hit, []):
            if uri is not None:
                occ_uri = getattr(occ, "uri", None)
                if occ_uri is not None and occ_uri != uri:
                    continue
            if occ.line == line and occ.column <= column < occ.column + len(occ.name):
                return hit, occ
        # Fallback: first same-line occurrence of key
        for occ in index.get(hit, []):
            if occ.line == line:
                return hit, occ

    if source is None:
        return None

    lines = source.split("\n")
    if line < 1 or line > len(lines):
        return None
    atom_line = lines[line - 1]

    best: tuple[tuple[str, int], Occurrence] | None = None
    best_span = None
    for (name, arity), occurrences in index.items():
        for occ in occurrences:
            if occ.line != line:
                continue
            if uri is not None:
                occ_uri = getattr(occ, "uri", None)
                if occ_uri is not None and occ_uri != uri:
                    continue
            start = occ.column  # 1-based
            # Span through closing paren when present, else just the name
            name_end = start + len(occ.name) - 1
            open_paren = atom_line.find("(", start - 1)
            if open_paren >= 0 and open_paren == start - 1 + len(occ.name):
                close = atom_line.find(")", open_paren + 1)
                end = close + 1 if close >= 0 else name_end
            else:
                end = name_end
            if start <= column <= end:
                span = end - start
                if best is None or span < (best_span or span + 1):
                    best = ((name, arity), occ)
                    best_span = span
    return best



def collect_occurrences(tree: lark.Tree | None) -> list[Occurrence]:
    if tree is None:
        return []

    occurrences: list[Occurrence] = []
    for statement_wrapper in tree.children:
        statement = statement_wrapper.children[0]
        if statement.data == "fact":
            _collect_atoms_with_role(statement.children[0], "fact", occurrences)
        elif statement.data == "rule":
            _collect_atoms_with_role(statement.children[0], "rule_head", occurrences)
            _collect_atoms_with_role(statement.children[1], "rule_body", occurrences)
        elif statement.data == "constraint":
            _collect_atoms_with_role(statement.children[0], "constraint", occurrences)
        elif statement.data == "show_directive":
            ident = statement.children[0]
            arity_tok = statement.children[1]
            occurrences.append(
                Occurrence(
                    name=str(ident),
                    arity=int(str(arity_tok)),
                    line=ident.line,
                    column=ident.column,
                    role="show",
                )
            )
        elif statement.data == "minimize_directive":
            for child in statement.children:
                _collect_atoms_with_role(child, "minimize", occurrences)
        elif statement.data == "external_directive":
            _collect_atoms_with_role(statement.children[0], "external", occurrences)
            if len(statement.children) > 1:
                _collect_atoms_with_role(statement.children[1], "external", occurrences)
        elif statement.data == "weak_constraint":
            # children: [body, weak_weight]
            _collect_atoms_with_role(statement.children[0], "weak", occurrences)
    return occurrences


def build_symbol_index(tree: lark.Tree | None) -> dict[tuple[str, int], list[Occurrence]]:
    index: dict[tuple[str, int], list[Occurrence]] = {}
    for occ in collect_occurrences(tree):
        index.setdefault((occ.name, occ.arity), []).append(occ)
    return index
