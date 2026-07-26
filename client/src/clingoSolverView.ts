import * as vscode from "vscode";
import {
  patchClingoConfigFile,
  resolveClingoConfig,
  updateClingoPath,
  updateClingoUsePath,
} from "./clingoConfig";
import {
  dedupePaths,
  isValidModels,
  removePathEntry,
  toWorkspaceRelativePath,
} from "./clingoConfigCore";
import type { ClingoResolvedConfig, ClingoRunOutcome } from "./clingoTypes";

type RerunMode = "first" | "all" | "config";

export class ClingoSolverView implements vscode.WebviewViewProvider {
  public static readonly viewType = "aspls.solver";

  private view?: vscode.WebviewView;
  private lastOutcome?: ClingoRunOutcome;
  private lastMode: RerunMode = "first";
  private lastFile?: string;

  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };
    webviewView.webview.html = this.renderHtml(this.lastOutcome);
    webviewView.webview.onDidReceiveMessage((message) => {
      void this.handleMessage(message);
    });
  }

  getLastMode(): RerunMode {
    return this.lastMode;
  }

  getLastFile(): string | undefined {
    return this.lastFile;
  }

  async showOutcome(
    outcome: ClingoRunOutcome,
    mode: RerunMode,
    file: string,
  ): Promise<void> {
    this.lastOutcome = outcome;
    this.lastMode = mode;
    this.lastFile = file;
    await vscode.commands.executeCommand("workbench.view.extension.aspls");
    try {
      await vscode.commands.executeCommand(
        `${ClingoSolverView.viewType}.focus`,
      );
    } catch {
      /* view may not be focusable until first resolve */
    }
    if (this.view) {
      this.view.show?.(true);
      this.refreshHtml();
    }
  }

  private refreshHtml(): void {
    if (this.view) {
      this.view.webview.html = this.renderHtml(this.lastOutcome);
    }
  }

  private async handleMessage(message: {
    type?: string;
    models?: unknown;
    usePath?: unknown;
    path?: unknown;
    text?: unknown;
  }): Promise<void> {
    try {
      switch (message?.type) {
        case "rerun":
          await vscode.commands.executeCommand("aspls.clingo.rerun");
          return;
        case "copy":
          if (typeof message.text === "string") {
            await vscode.env.clipboard.writeText(message.text);
            void vscode.window.setStatusBarMessage("Copied to clipboard", 1500);
          }
          return;
        case "setModels": {
          if (!isValidModels(message.models)) {
            return;
          }
          await patchClingoConfigFile({ models: message.models });
          break;
        }
        case "setUsePath": {
          if (typeof message.usePath !== "boolean") {
            return;
          }
          await updateClingoUsePath(message.usePath);
          break;
        }
        case "pickPath": {
          const picked = await vscode.window.showOpenDialog({
            canSelectMany: false,
            openLabel: "Use Clingo binary",
          });
          if (!picked || picked.length === 0) {
            return;
          }
          await updateClingoPath(picked[0].fsPath);
          break;
        }
        case "clearPath":
          await updateClingoPath("");
          break;
        case "addFiles": {
          const picked = await vscode.window.showOpenDialog({
            canSelectMany: true,
            openLabel: "Add ASP files",
            filters: { "ASP files": ["lp", "asp"] },
          });
          if (!picked || picked.length === 0) {
            return;
          }
          const cfg = resolveClingoConfig();
          const root =
            vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "";
          const added = picked.map((uri) =>
            root
              ? toWorkspaceRelativePath(uri.fsPath, root)
              : uri.fsPath,
          );
          const next = dedupePaths([...cfg.additionalFiles, ...added]);
          await patchClingoConfigFile({ additionalFiles: next });
          break;
        }
        case "removeFile": {
          if (typeof message.path !== "string") {
            return;
          }
          const cfg = resolveClingoConfig();
          const next = removePathEntry(cfg.additionalFiles, message.path);
          await patchClingoConfigFile({ additionalFiles: next });
          break;
        }
        default:
          return;
      }
      this.refreshHtml();
    } catch (err) {
      void vscode.window.showErrorMessage(
        `Clingo config update failed: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  private renderHtml(outcome: ClingoRunOutcome | undefined): string {
    const nonce = getNonce();
    let config: ClingoResolvedConfig | undefined;
    let configError: string | undefined;
    try {
      config = resolveClingoConfig();
    } catch (err) {
      configError = err instanceof Error ? err.message : String(err);
    }
    const hasWorkspace =
      !!vscode.workspace.workspaceFolders &&
      vscode.workspace.workspaceFolders.length > 0;
    const controls = this.renderControls(config, configError, hasWorkspace);
    const body = outcome ? this.renderOutcome(outcome) : this.renderEmpty();
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ASP Results</title>
  <style nonce="${nonce}">
    :root {
      color-scheme: light dark;
      --gap: 12px;
      --radius: 6px;
    }
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background, var(--vscode-editor-background));
      margin: 0;
      padding: var(--gap);
      line-height: 1.45;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: var(--gap);
    }
    h1 {
      font-size: 1rem;
      font-weight: 600;
      margin: 0;
    }
    .meta {
      color: var(--vscode-descriptionForeground);
      font-size: 0.85em;
      margin: 0 0 var(--gap);
      word-break: break-word;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    button {
      font: inherit;
      cursor: pointer;
      border: 1px solid var(--vscode-button-border, transparent);
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      padding: 4px 10px;
      border-radius: var(--radius);
    }
    button.primary {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
    }
    button:hover {
      filter: brightness(1.08);
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.8em;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .ok { background: color-mix(in srgb, #3f9d6a 30%, transparent); }
    .fail { background: color-mix(in srgb, #d4775a 35%, transparent); }
    .warn-box, .error-box, .set {
      border: 1px solid var(--vscode-panel-border, rgba(127,127,127,0.35));
      border-radius: var(--radius);
      padding: 10px;
      margin-bottom: 10px;
      background: var(--vscode-editor-background);
    }
    .error-box {
      border-color: color-mix(in srgb, #d4775a 60%, transparent);
    }
    .set-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }
    .set-head strong { font-size: 0.95em; }
    pre, code {
      font-family: var(--vscode-editor-font-family, ui-monospace, monospace);
      font-size: var(--vscode-editor-font-size, 12px);
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }
    .atoms {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .atom {
      background: color-mix(in srgb, var(--vscode-editor-selectionBackground) 55%, transparent);
      padding: 2px 7px;
      border-radius: 4px;
    }
    .empty {
      color: var(--vscode-descriptionForeground);
    }
    .controls {
      border: 1px solid var(--vscode-panel-border, rgba(127,127,127,0.35));
      border-radius: var(--radius);
      padding: 10px;
      margin-bottom: var(--gap);
      background: var(--vscode-editor-background);
    }
    .controls h2 {
      font-size: 0.95rem;
      margin: 0 0 8px;
    }
    .controls .row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
    }
    .controls .hint {
      color: var(--vscode-descriptionForeground);
      font-size: 0.8em;
      margin: -4px 0 8px;
    }
    .controls input[type="number"] {
      width: 4.5rem;
      font: inherit;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border, transparent);
      padding: 2px 6px;
      border-radius: 4px;
    }
    .controls .dimmed { opacity: 0.55; }
    .controls .path-text {
      flex: 1 1 100%;
      word-break: break-all;
      font-size: 0.85em;
    }
    .controls .file-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .controls .file-list li {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
  </style>
</head>
<body>
  ${controls}${body}
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    document.addEventListener('click', (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const action = t.getAttribute('data-action');
      if (action === 'rerun') {
        vscode.postMessage({ type: 'rerun' });
      } else if (action === 'copy') {
        const encoded = t.getAttribute('data-text') || '';
        let text = '';
        try { text = decodeURIComponent(encoded); } catch { text = encoded; }
        vscode.postMessage({ type: 'copy', text });
      } else if (action === 'pickPath') {
        vscode.postMessage({ type: 'pickPath' });
      } else if (action === 'clearPath') {
        vscode.postMessage({ type: 'clearPath' });
      } else if (action === 'addFiles') {
        vscode.postMessage({ type: 'addFiles' });
      } else if (action === 'removeFile') {
        const p = t.getAttribute('data-path') || '';
        vscode.postMessage({ type: 'removeFile', path: p });
      }
    });
    document.addEventListener('change', (e) => {
      const t = e.target;
      if (!(t instanceof HTMLInputElement)) return;
      const action = t.getAttribute('data-action');
      if (action === 'usePath') {
        vscode.postMessage({ type: 'setUsePath', usePath: t.checked });
      } else if (action === 'models') {
        const n = Number(t.value);
        vscode.postMessage({ type: 'setModels', models: n });
      }
    });
  </script>
</body>
</html>`;
  }

  private renderControls(
    config: ClingoResolvedConfig | undefined,
    configError: string | undefined,
    hasWorkspace: boolean,
  ): string {
    if (configError) {
      return `<section class="controls"><p class="empty">${escapeHtml(configError)}</p></section>`;
    }
    if (!config) {
      return "";
    }
    const pathDisabled = config.usePath ? "" : "disabled";
    const pathDisplay = config.clingoPath
      ? escapeHtml(config.clingoPath)
      : '<span class="empty">(default: clingo on PATH)</span>';
    const jsonNote = hasWorkspace
      ? ""
      : `<p class="empty">Open a workspace folder to edit models and additional files.</p>`;
    const modelsDisabled = hasWorkspace ? "" : "disabled";
    const fileButtonsDisabled = hasWorkspace ? "" : "disabled";
    const filesHtml =
      config.additionalFiles.length === 0
        ? `<p class="empty">None</p>`
        : `<ul class="file-list">${config.additionalFiles
            .map(
              (f) => `<li>
  <code>${escapeHtml(f)}</code>
  <button type="button" data-action="removeFile" data-path="${escapeHtml(f)}" ${fileButtonsDisabled}>Remove</button>
</li>`,
            )
            .join("")}</ul>`;

    return `<section class="controls">
  <h2>Controls</h2>
  ${jsonNote}
  <label class="row">Models
    <input type="number" min="0" step="1" value="${config.models}" data-action="models" ${modelsDisabled} />
  </label>
  <p class="hint">Used by Config runs (0 = all). First / All ignore this.</p>
  <label class="row">
    <input type="checkbox" data-action="usePath" ${config.usePath ? "checked" : ""} />
    Use native Clingo
  </label>
  <div class="row path-row ${config.usePath ? "" : "dimmed"}">
    <div class="path-text">Path: ${pathDisplay}</div>
    <div class="actions">
      <button type="button" data-action="pickPath" ${pathDisabled}>Browse</button>
      <button type="button" data-action="clearPath" ${pathDisabled}>Clear</button>
    </div>
  </div>
  <div class="files">
    <div class="row"><strong>Additional files</strong>
      <button type="button" data-action="addFiles" ${fileButtonsDisabled}>Add files</button>
    </div>
    ${filesHtml}
  </div>
</section>`;
  }

  private renderEmpty(): string {
    return `
<header>
  <h1>ASP Results</h1>
</header>
<p class="empty">Use the Solver view title actions — <strong>First</strong>, <strong>All</strong>, or <strong>Config</strong> — on a <code>.lp</code> / <code>.asp</code> file, or run from the editor context menu.</p>`;
  }

  private renderOutcome(outcome: ClingoRunOutcome): string {
    if (!outcome.ok) {
      return `
<header>
  <h1>ASP Results <span class="badge fail">ERROR</span></h1>
  <div class="actions">
    <button class="primary" data-action="rerun">Re-run</button>
    <button data-action="copy" data-text="${encodeCopy(outcome.error)}">Copy error</button>
  </div>
</header>
<p class="meta">${escapeHtml(outcome.commandSummary)} · ${escapeHtml(outcome.backend)}</p>
<div class="error-box"><pre>${escapeHtml(outcome.error)}</pre></div>
${outcome.raw ? `<details><summary>Raw output</summary><pre>${escapeHtml(outcome.raw)}</pre></details>` : ""}`;
    }

    const allAtoms = outcome.answerSets
      .map(
        (s) =>
          `Answer: ${s.index}\n${s.atoms.join(" ")}${s.costs ? `\nCost: ${s.costs.join(" ")}` : ""}`,
      )
      .join("\n\n");

    const setsHtml =
      outcome.answerSets.length === 0
        ? `<p class="empty">No answer sets.</p>`
        : outcome.answerSets
            .map((set) => {
              const text = set.atoms.join(" ");
              const atoms =
                set.atoms.length === 0
                  ? `<span class="empty">(empty)</span>`
                  : `<div class="atoms">${set.atoms
                      .map((a) => `<span class="atom">${escapeHtml(a)}</span>`)
                      .join("")}</div>`;
              const cost =
                set.costs && set.costs.length > 0
                  ? `<div class="meta">Cost: ${escapeHtml(set.costs.join(" "))}</div>`
                  : "";
              return `<section class="set">
  <div class="set-head">
    <strong>Answer set ${set.index}</strong>
    <button data-action="copy" data-text="${encodeCopy(text)}">Copy</button>
  </div>
  ${atoms}
  ${cost}
</section>`;
            })
            .join("");

    const warnings =
      outcome.warnings.length > 0
        ? `<div class="warn-box"><pre>${escapeHtml(outcome.warnings.join("\n\n"))}</pre></div>`
        : "";

    const more = outcome.more ? " (more)" : "";
    const time =
      outcome.timeTotal !== undefined
        ? ` · ${outcome.timeTotal.toFixed(3)}s`
        : "";

    return `
<header>
  <h1>ASP Results <span class="badge ok">${escapeHtml(outcome.result)}</span></h1>
  <div class="actions">
    <button class="primary" data-action="rerun">Re-run</button>
    <button data-action="copy" data-text="${encodeCopy(allAtoms)}">Copy all</button>
  </div>
</header>
<p class="meta">${escapeHtml(outcome.solver ?? "Clingo")} · ${escapeHtml(outcome.backend)} · models ${outcome.modelCount}${more}${time}<br/>${escapeHtml(outcome.commandSummary)}</p>
${warnings}
${setsHtml}`;
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function encodeCopy(text: string): string {
  return encodeURIComponent(text);
}

function getNonce(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let nonce = "";
  for (let i = 0; i < 32; i++) {
    nonce += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return nonce;
}
