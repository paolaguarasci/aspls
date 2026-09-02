import * as vscode from "vscode";
import { runFromDocument } from "./clingoCommands";
import type { ClingoSolverView } from "./clingoSolverView";

export function registerCodeLensCommands(
  context: vscode.ExtensionContext,
  panel: ClingoSolverView,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "aspls.codeLens.runFile",
      async (uriString: string) => {
        const uri = vscode.Uri.parse(uriString);
        const doc = await vscode.workspace.openTextDocument(uri);
        await runFromDocument(panel, doc, "config");
      },
    ),
    vscode.commands.registerCommand(
      "aspls.codeLens.showReferences",
      async (uriString: string, line: number, character: number) => {
        const uri = vscode.Uri.parse(uriString);
        const doc = await vscode.workspace.openTextDocument(uri);
        const editor = await vscode.window.showTextDocument(doc);
        const pos = new vscode.Position(line, character);
        editor.selection = new vscode.Selection(pos, pos);
        const locations = await vscode.commands.executeCommand<
          vscode.Location[]
        >("vscode.executeReferenceProvider", uri, pos);
        if (!locations?.length) {
          return;
        }
        await vscode.commands.executeCommand(
          "editor.action.showReferences",
          uri,
          pos,
          locations,
        );
      },
    ),
  );
}
