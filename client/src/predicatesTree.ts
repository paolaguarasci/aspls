import * as vscode from "vscode";
import {
  mapDocumentSymbols,
  type PredicateTreeNode,
  type RangeLike,
} from "./predicatesTreeMap";

function rangeLikeToVscode(range: RangeLike): vscode.Range {
  return new vscode.Range(
    range.start.line,
    range.start.character,
    range.end.line,
    range.end.character,
  );
}

export class PredicatesTreeProvider
  implements vscode.TreeDataProvider<PredicateTreeNode>
{
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<
    PredicateTreeNode | undefined | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  private debounce: NodeJS.Timeout | undefined;

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  scheduleRefresh(): void {
    clearTimeout(this.debounce);
    this.debounce = setTimeout(() => this.refresh(), 200);
  }

  getTreeItem(element: PredicateTreeNode): vscode.TreeItem {
    if (element.kind === "message") {
      const item = new vscode.TreeItem(
        element.label,
        vscode.TreeItemCollapsibleState.None,
      );
      item.contextValue = "aspls.predicates.message";
      return item;
    }

    const collapsible =
      element.kind === "occurrence"
        ? vscode.TreeItemCollapsibleState.None
        : element.children?.length
          ? vscode.TreeItemCollapsibleState.Collapsed
          : vscode.TreeItemCollapsibleState.None;

    const item = new vscode.TreeItem(element.label, collapsible);
    item.description = element.detail;

    if (
      (element.kind === "predicate" || element.kind === "occurrence") &&
      element.uri &&
      element.range
    ) {
      item.command = {
        command: "vscode.open",
        title: "Open",
        arguments: [
          vscode.Uri.parse(element.uri),
          { selection: rangeLikeToVscode(element.range) },
        ],
      };
    }

    item.contextValue = `aspls.predicates.${element.kind}`;
    return item;
  }

  async getChildren(element?: PredicateTreeNode): Promise<PredicateTreeNode[]> {
    if (element && element.kind !== "message" && element.children?.length) {
      return element.children;
    }
    if (element) return [];

    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== "asp") {
      return [
        {
          kind: "message",
          label: "Open an ASP file (.lp / .asp)",
        },
      ];
    }
    try {
      const symbols =
        (await vscode.commands.executeCommand<vscode.DocumentSymbol[]>(
          "vscode.executeDocumentSymbolProvider",
          editor.document.uri,
        )) ?? [];
      if (symbols.length === 0) {
        return [
          {
            kind: "message",
            label: "No predicates in this file",
          },
        ];
      }
      return mapDocumentSymbols(symbols, editor.document.uri.toString());
    } catch {
      return [
        {
          kind: "message",
          label: "Predicates unavailable (language server not ready)",
        },
      ];
    }
  }
}

export function registerPredicatesTree(
  context: vscode.ExtensionContext,
): PredicatesTreeProvider {
  const provider = new PredicatesTreeProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("aspls.predicates", provider),
    vscode.window.onDidChangeActiveTextEditor(() => provider.refresh()),
    vscode.workspace.onDidChangeTextDocument((e) => {
      const active = vscode.window.activeTextEditor?.document;
      if (active && e.document.uri.toString() === active.uri.toString()) {
        provider.scheduleRefresh();
      }
    }),
  );
  return provider;
}
