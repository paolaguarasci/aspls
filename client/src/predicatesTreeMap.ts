export type RangeLike = {
  start: { line: number; character: number };
  end: { line: number; character: number };
};

export type PredicateTreeNode =
  | { kind: "message"; label: string }
  | {
      kind: "predicate" | "role" | "occurrence";
      label: string;
      detail?: string;
      uri?: string;
      range?: RangeLike;
      children?: PredicateTreeNode[];
    };

export type WorkspacePredicateNode = {
  name: string;
  kind: "predicate" | "role" | "occurrence";
  detail?: string;
  uri?: string;
  range?: RangeLike;
  negated?: boolean;
  children?: WorkspacePredicateNode[];
};

export type SymbolLike = {
  name: string;
  detail?: string;
  selectionRange: RangeLike;
  children?: SymbolLike[];
};

function mapSymbolChildren(
  children: SymbolLike[] | undefined,
  uri: string,
  depth: 1 | 2,
): PredicateTreeNode[] | undefined {
  if (!children?.length) return undefined;
  const kind = depth === 1 ? "role" : "occurrence";
  return children.map((c) => ({
    kind,
    label: c.name,
    detail: c.detail,
    uri,
    range: c.selectionRange,
    children:
      depth === 1 ? mapSymbolChildren(c.children, uri, 2) : undefined,
  }));
}

export function mapDocumentSymbols(
  symbols: Array<{
    name: string;
    detail?: string;
    selectionRange: RangeLike;
    children?: SymbolLike[];
  }>,
  uri: string,
): PredicateTreeNode[] {
  return symbols.map((s) => ({
    kind: "predicate" as const,
    label: s.name,
    detail: s.detail,
    uri,
    range: s.selectionRange,
    children: mapSymbolChildren(s.children, uri, 1),
  }));
}

function mapWorkspaceNode(node: WorkspacePredicateNode): PredicateTreeNode {
  const children = node.children?.length
    ? node.children.map(mapWorkspaceNode)
    : undefined;
  return {
    kind: node.kind,
    label: node.name,
    detail: node.detail,
    uri: node.uri,
    range: node.range,
    children,
  };
}

export function mapWorkspaceNodes(
  nodes: WorkspacePredicateNode[],
): PredicateTreeNode[] {
  return nodes.map(mapWorkspaceNode);
}
