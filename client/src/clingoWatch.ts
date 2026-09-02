import * as vscode from "vscode";
import {
  resolveAdditionalFiles,
  resolveClingoConfig,
} from "./clingoConfig";
import type { ClingoSolverView } from "./clingoSolverView";
import {
  buildWatchPool,
  normalizeWatchDebounceMs,
  shouldWatchRerun,
} from "./clingoWatchCore";
import { runFromDocument } from "./clingoCommands";

export function registerClingoWatch(
  context: vscode.ExtensionContext,
  panel: ClingoSolverView,
): void {
  let debounceTimer: NodeJS.Timeout | undefined;
  let pendingDocument: vscode.TextDocument | undefined;

  const scheduleWatchRerun = (document: vscode.TextDocument): void => {
    clearTimeout(debounceTimer);
    pendingDocument = document;
    const debounceMs = normalizeWatchDebounceMs(
      vscode.workspace
        .getConfiguration("aspls")
        .get<number>("clingo.watchDebounceMs"),
    );
    debounceTimer = setTimeout(() => {
      const doc = pendingDocument;
      pendingDocument = undefined;
      if (doc) {
        void runFromDocument(panel, doc, panel.getLastMode(), { quiet: true });
      }
    }, debounceMs);
  };

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (document.languageId !== "asp") {
        return;
      }
      const watchEnabled = vscode.workspace
        .getConfiguration("aspls")
        .get<boolean>("clingo.watchOnSave");
      if (!watchEnabled) {
        return;
      }
      const lastFile = panel.getLastFile();
      if (!lastFile) {
        return;
      }
      const config = resolveClingoConfig();
      const additionalFiles = resolveAdditionalFiles(
        lastFile,
        config.additionalFiles,
      );
      const pool = buildWatchPool(lastFile, additionalFiles);
      if (
        !shouldWatchRerun(
          true,
          lastFile,
          document.uri.fsPath,
          pool,
        )
      ) {
        return;
      }
      scheduleWatchRerun(document);
    }),
    { dispose: () => clearTimeout(debounceTimer) },
  );
}
