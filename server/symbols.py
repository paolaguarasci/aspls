from dataclasses import dataclass

import lark

DEFINING_ROLES = frozenset({"fact", "rule_head"})
USING_ROLES = frozenset({"rule_body", "constraint", "minimize"})


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
    index: dict[tuple[str, int], list[Occurrence]], line: int, column: int
) -> tuple[str, int] | None:
    for (name, arity), occurrences in index.items():
        for occ in occurrences:
            token_end_column = occ.column + len(occ.name)
            if occ.line == line and occ.column <= column < token_end_column:
                return (name, arity)
    return None


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
    return occurrences


def build_symbol_index(tree: lark.Tree | None) -> dict[tuple[str, int], list[Occurrence]]:
    index: dict[tuple[str, int], list[Occurrence]] = {}
    for occ in collect_occurrences(tree):
        index.setdefault((occ.name, occ.arity), []).append(occ)
    return index
