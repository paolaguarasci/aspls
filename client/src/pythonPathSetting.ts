import * as vscode from "vscode";

/**
 * The user's own aspls.pythonPath. Workspace values are ignored: a workspace
 * must never choose the executable that the extension runs.
 */
export function configuredPythonPath(): string | undefined {
  return vscode.workspace.getConfiguration("aspls").inspect<string>("pythonPath")?.globalValue;
}
