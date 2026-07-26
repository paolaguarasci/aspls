import * as path from "path";
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from "vscode-languageclient/node";
import { registerClingoCommands } from "./clingoCommands";
import { registerCookbookCommands } from "./cookbook/cookbookCommands";
import { ClingoSolverView } from "./clingoSolverView";
import { findPythonInterpreter, ensureServerVenv } from "./pythonSetup";
import { PredicateRainbow } from "./predicateRainbowDecorations";
import { registerPredicatesTree } from "./predicatesTree";

let client: LanguageClient | undefined;
let rainbow: PredicateRainbow | undefined;

export async function activate(
  context: vscode.ExtensionContext,
): Promise<void> {
  rainbow = new PredicateRainbow();
  rainbow.start();
  context.subscriptions.push({ dispose: () => rainbow?.dispose() });

  const solverView = new ClingoSolverView(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      ClingoSolverView.viewType,
      solverView,
    ),
  );
  registerClingoCommands(context, solverView);
  registerCookbookCommands(context);

  const predicatesProvider = registerPredicatesTree(context, () => client);
  await startLanguageServer(context, predicatesProvider);
}

async function startLanguageServer(
  context: vscode.ExtensionContext,
  predicatesProvider: ReturnType<typeof registerPredicatesTree>,
): Promise<void> {
  const config = vscode.workspace.getConfiguration("aspls");
  const configuredPath = config.get<string>("pythonPath");

  const pythonInterpreter = await findPythonInterpreter(configuredPath);
  if (!pythonInterpreter) {
    vscode.window.showErrorMessage(
      "ASP Language Server: no Python 3 interpreter found. Install Python 3 and/or set 'aspls.pythonPath'. Clingo run commands still work.",
    );
    return;
  }

  const requirementsPath = context.asAbsolutePath("server-requirements.txt");
  let venvPython: string;
  try {
    venvPython = await ensureServerVenv(
      context.globalStorageUri.fsPath,
      pythonInterpreter,
      requirementsPath,
    );
  } catch (err) {
    vscode.window.showErrorMessage(String(err));
    return;
  }

  const serverModulePath = context.asAbsolutePath(
    path.join("server", "server.py"),
  );
  const serverOptions: ServerOptions = {
    command: venvPython,
    args: [serverModulePath],
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "asp" }],
    synchronize: {
      configurationSection: "aspls",
    },
  };

  client = new LanguageClient(
    "aspls",
    "ASP Language Server",
    serverOptions,
    clientOptions,
  );
  await client.start();
  predicatesProvider.refresh();
}

export async function deactivate(): Promise<void> {
  rainbow?.dispose();
  rainbow = undefined;
  if (client) {
    await client.stop();
  }
}
