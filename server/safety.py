from __future__ import annotations

from dataclasses import dataclass

import lark


@dataclass
class UnsafeFinding:
    line: int
    column: int
    variables: list[str]


def _collect_vars(node, out: list[tuple[str, int, int]], *, under_negation: bool = False) -> None:
    if isinstance(node, lark.Token):
        # Bare VARIABLE in range_bound (grammar: INT | IDENTIFIER | VARIABLE).
        if node.type == "VARIABLE":
            out.append((str(node), node.line, node.column))
        return
    if not isinstance(node, lark.Tree):
        return
    if node.data == "var_term":
        tok = node.children[0]
        out.append((str(tok), tok.line, tok.column))
        return
    if node.data == "negated_literal":
        for child in node.children:
            _collect_vars(child, out, under_negation=True)
        return
    for child in node.children:
        _collect_vars(child, out, under_negation=under_negation)


def _var_names(node) -> set[str]:
    found: list[tuple[str, int, int]] = []
    _collect_vars(node, found)
    return {name for name, _, _ in found}


def _single_var(node) -> str | None:
    if isinstance(node, lark.Tree) and node.data == "var_term":
        return str(node.children[0])
    return None


def _compare_parts(node: lark.Tree) -> tuple[str, lark.Tree | lark.Token, lark.Tree | lark.Token] | None:
    """Return (op, left, right) for a comparison tree, or None."""
    if node.data == "term_cmp_term":
        left, op, right = node.children
        return str(op), left, right
    if node.data == "term_cmp_aggregate":
        left, op, right = node.children
        return str(op), left, right
    if node.data == "aggregate_cmp_term":
        left, op, right = node.children
        return str(op), left, right
    if node.data == "comparison":
        # Unaliased comparison wrapper — should not appear with → aliases, but be defensive.
        for child in node.children:
            if isinstance(child, lark.Tree):
                return _compare_parts(child)
    return None


def _add_positive_atom_binders(node, out: set[str]) -> None:
    """Variables appearing in positive ordinary atoms (not under not, not in comparisons/aggs)."""
    if not isinstance(node, lark.Tree):
        return
    if node.data == "negated_literal":
        return
    if node.data in ("compound_atom", "nullary_atom"):
        out |= _var_names(node)
        return
    if node.data in (
        "aggregate",
        "aggregate_cmp_term",
        "term_cmp_aggregate",
        "term_cmp_term",
        "comparison",
    ):
        return
    for child in node.children:
        _add_positive_atom_binders(child, out)


def _aggregate_elems(aggregate: lark.Tree) -> list[lark.Tree]:
    return [c for c in aggregate.children if isinstance(c, lark.Tree) and c.data == "aggregate_elem"]


def _mark_aggregate_local_safe(aggregate: lark.Tree, global_safe: set[str], safe: set[str]) -> bool:
    """Mark vars that are safe inside aggregate elements. Return True if any elem is fully safe.

    Clingo: ``#count{ X : node(X) }`` binds X via the condition.
    Clingo: ``#count{ node(X) }`` is a term tuple with empty condition → X not bound here.
    """
    any_elem_ok = False
    for elem in _aggregate_elems(aggregate):
        children = [c for c in elem.children if isinstance(c, lark.Tree)]
        if len(children) >= 2 and children[0].data == "term_tuple":
            term_tuple, body = children[0], children[1]
            local = set(global_safe)
            _add_positive_atom_binders(body, local)
            _saturate_eq_binders(body, local)
            elem_vars = _var_names(term_tuple) | _var_names(body)
            if elem_vars <= local:
                any_elem_ok = True
                safe |= elem_vars
            else:
                # Still mark the ones that are locally bound.
                safe |= elem_vars & local
        # Body-only element: Clingo treats literals as terms with empty condition — no binders.
    return any_elem_ok or not _aggregate_elems(aggregate)


def _aggregate_locals_safe(aggregate: lark.Tree, global_safe: set[str]) -> bool:
    """True if every variable inside the aggregate is safe under global_safe."""
    for elem in _aggregate_elems(aggregate):
        children = [c for c in elem.children if isinstance(c, lark.Tree)]
        if len(children) >= 2 and children[0].data == "term_tuple":
            term_tuple, body = children[0], children[1]
            local = set(global_safe)
            _add_positive_atom_binders(body, local)
            _saturate_eq_binders(body, local)
            if not (_var_names(term_tuple) | _var_names(body)) <= local:
                return False
        else:
            # Body-only → terms with empty condition: vars must already be globally safe.
            if not _var_names(elem) <= global_safe:
                return False
    return True


def _apply_eq_binders_once(node, safe: set[str]) -> bool:
    """One scan: bind variables via ``Var = Term`` / ``Term = Var`` / aggregate assignment."""
    if not isinstance(node, lark.Tree):
        return False
    if node.data == "negated_literal":
        return False

    changed = False
    parts = _compare_parts(node)
    if parts is not None:
        op, left, right = parts
        # Always resolve aggregate-local binders inside comparisons.
        for side in (left, right):
            if isinstance(side, lark.Tree) and side.data == "aggregate":
                before = set(safe)
                _mark_aggregate_local_safe(side, set(safe), safe)
                if safe != before:
                    changed = True
        if op == "=":
            lv = _single_var(left)
            rv = _single_var(right)
            if lv is not None and _var_names(right) <= safe and lv not in safe:
                safe.add(lv)
                changed = True
            if rv is not None and _var_names(left) <= safe and rv not in safe:
                safe.add(rv)
                changed = True
            # Var = Aggregate / Aggregate = Var (right/left already marked above)
            if lv is not None and isinstance(right, lark.Tree) and right.data == "aggregate":
                if _aggregate_locals_safe(right, safe) and lv not in safe:
                    safe.add(lv)
                    changed = True
            if rv is not None and isinstance(left, lark.Tree) and left.data == "aggregate":
                if _aggregate_locals_safe(left, safe) and rv not in safe:
                    safe.add(rv)
                    changed = True
        return changed

    if node.data == "aggregate":
        before = set(safe)
        _mark_aggregate_local_safe(node, set(safe), safe)
        return safe != before

    for child in node.children:
        if _apply_eq_binders_once(child, safe):
            changed = True
    return changed


def _saturate_eq_binders(node, safe: set[str]) -> None:
    """Fixed-point of equality/aggregate assignment binders (Clingo-style)."""
    while _apply_eq_binders_once(node, safe):
        pass


def _collect_safe_vars(body: lark.Tree) -> set[str]:
    safe: set[str] = set()
    _add_positive_atom_binders(body, safe)
    _saturate_eq_binders(body, safe)
    return safe


def _finding_for_vars(var_occurrences: list[tuple[str, int, int]], unsafe: set[str]) -> UnsafeFinding | None:
    if not unsafe:
        return None
    ordered = sorted(unsafe)
    for name, line, column in var_occurrences:
        if name in unsafe:
            return UnsafeFinding(line=line, column=column, variables=ordered)
    return UnsafeFinding(line=1, column=1, variables=ordered)


def _check_weak_constraint(statement: lark.Tree) -> UnsafeFinding | None:
    body, weight = statement.children[0], statement.children[1]
    all_vars: list[tuple[str, int, int]] = []
    _collect_vars(body, all_vars)
    _collect_vars(weight, all_vars)
    safe = _collect_safe_vars(body)
    names = {n for n, _, _ in all_vars}
    return _finding_for_vars(all_vars, names - safe)


def _check_rule_or_constraint(statement: lark.Tree) -> UnsafeFinding | None:
    all_vars: list[tuple[str, int, int]] = []
    safe: set[str] = set()
    if statement.data == "rule":
        head, body = statement.children[0], statement.children[1]
        _collect_vars(head, all_vars)
        _collect_vars(body, all_vars)
        safe = _collect_safe_vars(body)
    elif statement.data == "constraint":
        body = statement.children[0]
        _collect_vars(body, all_vars)
        safe = _collect_safe_vars(body)
    elif statement.data == "fact":
        head = statement.children[0]
        _collect_vars(head, all_vars)
        # Facts have no body binders.
        safe = set()
    else:
        return None
    names = {n for n, _, _ in all_vars}
    return _finding_for_vars(all_vars, names - safe)


def find_unsafe_variables(tree: lark.Tree | None) -> list[UnsafeFinding]:
    if tree is None:
        return []
    findings: list[UnsafeFinding] = []
    for statement_wrapper in tree.children:
        statement = statement_wrapper.children[0]
        # Unwrap fact/rule/constraint aliases from grammar rule names
        data = statement.data
        if data in ("fact", "rule", "constraint"):
            found = _check_rule_or_constraint(statement)
            if found:
                findings.append(found)
        elif data == "weak_constraint":
            found = _check_weak_constraint(statement)
            if found:
                findings.append(found)
    return findings
