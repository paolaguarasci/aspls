import * as vscode from "vscode";
import { findPythonInterpreter } from "./pythonSetup";
import {
  GroundingDebugSession,
  resolveGroundingDebugScript,
} from "./groundingDebugAdapter";
import { trackFeature } from "./telemetry";

const DEBUG_TYPE = "aspls-grounding";

export function registerGroundingDebug(context: vscode.ExtensionContext): void {
  const factory = new GroundingDebugAdapterFactory(context);
  context.subscriptions.push(
    vscode.debug.registerDebugAdapterDescriptorFactory(DEBUG_TYPE, factory),
    vscode.debug.registerDebugConfigurationProvider(DEBUG_TYPE, {
      resolveDebugConfiguration(
        _folder: vscode.WorkspaceFolder | undefined,
        config: vscode.DebugConfiguration,
      ): vscode.DebugConfiguration | undefined {
        if (!config.type) {
          return undefined;
        }
        const editor = vscode.window.activeTextEditor;
        if (!config.program && editor?.document.languageId === "asp") {
          config.program = editor.document.uri.fsPath;
        }
        if (!config.program) {
          void vscode.window.showErrorMessage(
            "Debug Grounding: open an .lp/.asp file or set \"program\" in launch.json.",
          );
          return undefined;
        }
        config.name = config.name ?? "Debug Grounding";
        return config;
      },
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("aspls.grounding.debug", async () => {
      trackFeature("grounding.debug");
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.document.languageId !== "asp") {
        void vscode.window.showErrorMessage(
          "Debug Grounding: open an ASP (.lp/.asp) file first.",
        );
        return;
      }
      await vscode.debug.startDebugging(undefined, {
        type: DEBUG_TYPE,
        request: "launch",
        name: "Debug Grounding",
        program: editor.document.uri.fsPath,
      });
    }),
  );
}

class GroundingDebugAdapterFactory
  implements vscode.DebugAdapterDescriptorFactory {
  constructor(private readonly context: vscode.ExtensionContext) { }

  async createDebugAdapterDescriptor(
    session: vscode.DebugSession,
  ): Promise<vscode.DebugAdapterDescriptor> {
    const config = vscode.workspace.getConfiguration("aspls");
    const configuredPath = config.get<string>("pythonPath");
    const pythonInterpreter = await findPythonInterpreter(configuredPath);
    if (!pythonInterpreter) {
      throw new Error(
        "Debug Grounding requires Python 3. Set aspls.pythonPath or install python3 on PATH.",
      );
    }

    const scriptPath = resolveGroundingDebugScript(this.context.extensionPath);
    return new vscode.DebugAdapterInlineImplementation(
      new GroundingDebugSession({
        pythonPath: pythonInterpreter,
        scriptPath,
      }),
    );
  }
}

export { DEBUG_TYPE };
