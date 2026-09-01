import * as vscode from "vscode";
import {
  resolveAdditionalFiles,
  resolveClingoConfig,
  writeSampleConfigFile,
} from "./clingoConfig";
import { buildClingoCustomArgs } from "./clingoConfigCore";
import { runClingo } from "./clingoRunner";
import type { ClingoSolverView } from "./clingoSolverView";
import type { ClingoRunRequest } from "./clingoTypes";

type RunMode = "first" | "all" | "config";

export function registerClingoCommands(
  context: vscode.ExtensionContext,
  panel: ClingoSolverView,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("aspls.clingo.computeFirst", () =>
      runFromEditor(panel, "first"),
    ),
    vscode.commands.registerCommand("aspls.clingo.computeAll", () =>
      runFromEditor(panel, "all"),
    ),
    vscode.commands.registerCommand("aspls.clingo.computeWithConfig", () =>
      runFromEditor(panel, "config"),
    ),
    vscode.commands.registerCommand("aspls.clingo.rerun", () =>
      rerun(panel),
    ),
    vscode.commands.registerCommand("aspls.clingo.initConfig", () =>
      initConfig(),
    ),
  );
}

async function initConfig(): Promise<void> {
  try {
    const cfg = resolveClingoConfig();
    const uri = await writeSampleConfigFile(cfg.configFileName);
    const doc = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(doc);
    void vscode.window.showInformationMessage(
      `Created ${cfg.configFileName}`,
    );
  } catch (err) {
    void vscode.window.showErrorMessage(String(err));
  }
}

async function rerun(panel: ClingoSolverView): Promise<void> {
  const mode = panel.getLastMode();
  const lastFile = panel.getLastFile();
  if (lastFile) {
    const doc = await vscode.workspace.openTextDocument(lastFile);
    await vscode.window.showTextDocument(doc, { preview: false });
  }
  await runFromEditor(panel, mode);
}

async function runFromEditor(
  panel: ClingoSolverView,
  mode: RunMode,
): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "asp") {
    void vscode.window.showErrorMessage(
      "Open an ASP (.lp / .asp) file to run Clingo.",
    );
    return;
  }

  if (editor.document.isDirty) {
    const saved = await editor.document.save();
    if (!saved) {
      void vscode.window.showWarningMessage(
        "Save the file before running Clingo.",
      );
      return;
    }
  }

  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "Running Clingo…",
        cancellable: false,
      },
      async () => {
        const request = buildRequest(editor.document, mode);
        const outcome = await runClingo(request);
        await panel.showOutcome(outcome, mode, editor.document.uri.fsPath);
        const capWarn = (outcome.ok ? outcome.warnings : outcome.warnings ?? [])
          .find((w) => w.startsWith("WASM capability warning"));
        if (capWarn) {
          void vscode.window.showWarningMessage(
            "Some customArgs are limited under WASM. Enable aspls.clingo.usePath for full Clingo CLI support.",
          );
        }
        if (!outcome.ok) {
          void vscode.window.showErrorMessage(
            `Clingo: ${outcome.error.split("\n")[0]}`,
          );
        }
      },
    );
  } catch (err) {
    void vscode.window.showErrorMessage(String(err));
  }
}

function buildRequest(
  document: vscode.TextDocument,
  mode: RunMode,
): ClingoRunRequest {
  const requireConfigFile = mode === "config";
  const config = resolveClingoConfig({ requireConfigFile });

  let models: number;
  if (mode === "first") {
    models = 1;
  } else if (mode === "all") {
    models = 0;
  } else {
    models = config.models;
  }

  const primaryFile = document.uri.fsPath;
  const additionalFiles = resolveAdditionalFiles(
    primaryFile,
    config.additionalFiles,
  );

  return {
    primaryFile,
    program: document.getText(),
    models,
    additionalFiles,
    threads: config.threads,
    customArgs: buildClingoCustomArgs({
      constants: config.constants,
      customArgs: config.customArgs,
    }),
    usePath: config.usePath,
    clingoPath: config.clingoPath,
  };
}
