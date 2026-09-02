import * as vscode from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { trackFeature } from "./telemetry";
import {
  mapDocumentSymbols,
  mapWorkspaceNodes,
  type PredicateTreeNode,
  type RangeLike,
  type WorkspacePredicateNode,
} from "./predicatesTreeMap";

const STATE_KEY = "aspls.predicates.workspaceMode";

function rangeLikeToVscode(range: RangeLike): vscode.Range {
  return new vscode.Range(
    range.start.line,
    range.start.character,
    range.end.line,
    range.end.character,
  );
}

export class PredicatesTreeProvider
  implements vscode.TreeDataProvider<PredicateTreeNode> {
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<
    PredicateTreeNode | undefined | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  private debounce: NodeJS.Timeout | undefined;

  constructor(
    private readonly context: vscode.ExtensionContext,
    private readonly getClient: () => LanguageClient | undefined,
  ) { }

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

    const workspaceMode = this.context.workspaceState.get<boolean>(
      STATE_KEY,
      false,
    );
    if (workspaceMode) {
      if (!vscode.workspace.workspaceFolders?.length) {
        return [
          {
            kind: "message",
            label: "Open a folder to browse workspace predicates",
          },
        ];
      }
      const client = this.getClient();
      if (!client) {
        return [
          {
            kind: "message",
            label: "Predicates unavailable (language server not ready)",
          },
        ];
      }
      try {
        const uri =
          vscode.window.activeTextEditor?.document.uri.toString() ?? null;
        const nodes = await client.sendRequest<WorkspacePredicateNode[]>(
          "aspls/workspacePredicates",
          { uri },
        );
        if (!nodes?.length) {
          return [
            {
              kind: "message",
              label: "No predicates in workspace",
            },
          ];
        }
        return mapWorkspaceNodes(nodes);
      } catch {
        return [
          {
            kind: "message",
            label: "Predicates unavailable (language server not ready)",
          },
        ];
      }
    }

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
  getClient: () => LanguageClient | undefined,
): PredicatesTreeProvider {
  const provider = new PredicatesTreeProvider(context, getClient);
  const syncContext = async () => {
    const on = context.workspaceState.get<boolean>(STATE_KEY, false);
    await vscode.commands.executeCommand(
      "setContext",
      "aspls.predicates.workspaceMode",
      on,
    );
  };
  void syncContext();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("aspls.predicates", provider),
    vscode.commands.registerCommand(
      "aspls.predicates.toggleWorkspace",
      async () => {
        trackFeature("predicates.toggleWorkspace");
        const cur = context.workspaceState.get<boolean>(STATE_KEY, false);
        await context.workspaceState.update(STATE_KEY, !cur);
        await syncContext();
        provider.refresh();
      },
    ),
    vscode.window.onDidChangeActiveTextEditor(() => provider.refresh()),
    vscode.workspace.onDidChangeTextDocument((e) => {
      if (context.workspaceState.get<boolean>(STATE_KEY, false)) {
        if (e.document.languageId === "asp") provider.scheduleRefresh();
        return;
      }
      const active = vscode.window.activeTextEditor?.document;
      if (active && e.document.uri.toString() === active.uri.toString()) {
        provider.scheduleRefresh();
      }
    }),
    vscode.workspace
      .createFileSystemWatcher("**/aspls.clingo.json")
      .onDidChange(() => {
        if (context.workspaceState.get<boolean>(STATE_KEY, false))
          provider.refresh();
      }),
  );
  return provider;
}
