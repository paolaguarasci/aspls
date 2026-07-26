import * as vscode from "vscode";
import type { ClingoRunOutcome } from "./clingoTypes";

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
      if (message?.type === "rerun") {
        void vscode.commands.executeCommand("aspls.clingo.rerun");
      } else if (message?.type === "copy" && typeof message.text === "string") {
        void vscode.env.clipboard.writeText(message.text);
        void vscode.window.setStatusBarMessage("Copied to clipboard", 1500);
      }
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
      this.view.webview.html = this.renderHtml(outcome);
    }
  }

  private renderHtml(outcome: ClingoRunOutcome | undefined): string {
    const nonce = getNonce();
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
  </style>
</head>
<body>
  ${body}
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
      }
    });
  </script>
</body>
</html>`;
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
