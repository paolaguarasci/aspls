from dataclasses import dataclass

import lark

HEAD_RULES = {"fact", "rule"}
HEAD_CONTAINER_RULES = {"head", "disjunction"}


@dataclass
class Occurrence:
    name: str
    arity: int
    line: int
    column: int
    role: str


def _atom_name_and_arity(atom_node: lark.Tree) -> tuple[str, int]:
    if atom_node.data == "compound_atom":
        name = str(atom_node.children[0])
        arity = len(atom_node.children) - 1
        return name, arity
    # nullary_atom
    name = str(atom_node.children[0])
    return name, 0


def _collect_atoms_with_role(node, role: str, out: list[Occurrence]) -> None:
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
                )
            )
            return
        for child in node.children:
            _collect_atoms_with_role(child, role, out)


def find_key_at(
    index: dict[tuple[str, int], list[Occurrence]], line: int, column: int
) -> tuple[str, int] | None:
    for (name, arity), occurrences in index.items():
        for occ in occurrences:
            token_end_column = occ.column + len(occ.name)
            if occ.line == line and occ.column <= column < token_end_column:
                return (name, arity)
    return None


def build_symbol_index(tree: lark.Tree | None) -> dict[tuple[str, int], list[Occurrence]]:
    index: dict[tuple[str, int], list[Occurrence]] = {}
    if tree is None:
        return index

    occurrences: list[Occurrence] = []
    for statement_wrapper in tree.children:
        statement = statement_wrapper.children[0]
        if statement.data in ("fact", "rule"):
            head_node = statement.children[0]
            _collect_atoms_with_role(head_node, "head", occurrences)
            if statement.data == "rule":
                body_node = statement.children[1]
                _collect_atoms_with_role(body_node, "body", occurrences)
        elif statement.data == "constraint":
            body_node = statement.children[0]
            _collect_atoms_with_role(body_node, "body", occurrences)

    for occ in occurrences:
        index.setdefault((occ.name, occ.arity), []).append(occ)

    return index
