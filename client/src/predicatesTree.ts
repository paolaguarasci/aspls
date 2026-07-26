import * as vscode from "vscode";

type PredicateItem =
  | { kind: "message"; label: string }
  | {
      kind: "predicate";
      label: string;
      detail?: string;
      location: vscode.Location;
    };

export class PredicatesTreeProvider
  implements vscode.TreeDataProvider<PredicateItem>
{
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<
    PredicateItem | undefined | void
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

  getTreeItem(element: PredicateItem): vscode.TreeItem {
    if (element.kind === "message") {
      const item = new vscode.TreeItem(
        element.label,
        vscode.TreeItemCollapsibleState.None,
      );
      item.contextValue = "aspls.predicates.message";
      return item;
    }
    const item = new vscode.TreeItem(
      element.label,
      vscode.TreeItemCollapsibleState.None,
    );
    item.description = element.detail;
    item.command = {
      command: "vscode.open",
      title: "Open",
      arguments: [
        element.location.uri,
        { selection: element.location.range },
      ],
    };
    item.contextValue = "aspls.predicates.predicate";
    return item;
  }

  async getChildren(element?: PredicateItem): Promise<PredicateItem[]> {
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
      return symbols.map((s) => ({
        kind: "predicate" as const,
        label: s.name,
        detail: s.detail,
        location: new vscode.Location(editor.document.uri, s.selectionRange),
      }));
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
