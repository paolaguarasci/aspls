import * as vscode from "vscode";
import { readClingoFileConfigState } from "./clingoConfig";
import { shouldWarnDeprecatedAdditionalFilesSetting } from "./clingoConfigCore";

const GLOBAL_STATE_KEY = "deprecation.additionalFiles.v1";

function settingsAdditionalFiles(): string[] {
  const raw = vscode.workspace
    .getConfiguration("aspls")
    .get<unknown>("clingo.additionalFiles", []);
  return Array.isArray(raw)
    ? raw.filter((v): v is string => typeof v === "string")
    : [];
}

function maybeShowDeprecationWarning(
  context: vscode.ExtensionContext,
): void {
  const fileState = readClingoFileConfigState();
  if (
    !shouldWarnDeprecatedAdditionalFilesSetting({
      settingsAdditionalFiles: settingsAdditionalFiles(),
      configAdditionalFilesDefined: fileState.additionalFilesDefined,
    })
  ) {
    return;
  }
  if (context.globalState.get<boolean>(GLOBAL_STATE_KEY)) {
    return;
  }
  void context.globalState.update(GLOBAL_STATE_KEY, true);
  void vscode.window
    .showWarningMessage(
      "aspls.clingo.additionalFiles is deprecated and no longer affects runs or the language server. " +
        "Add files to your workspace Clingo config (aspls.clingo.json) instead.",
      "Create config file",
    )
    .then((choice) => {
      if (choice === "Create config file") {
        void vscode.commands.executeCommand("aspls.clingo.initConfig");
      }
    });
}

/** Non-invasive, once-per-install warning when settings-only additionalFiles are in use. */
export function registerAdditionalFilesDeprecationWarning(
  context: vscode.ExtensionContext,
): void {
  maybeShowDeprecationWarning(context);
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (
        event.affectsConfiguration("aspls.clingo.additionalFiles") ||
        event.affectsConfiguration("aspls.clingo.configFile")
      ) {
        maybeShowDeprecationWarning(context);
      }
    }),
  );
}
