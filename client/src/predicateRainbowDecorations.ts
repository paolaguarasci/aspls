import * as vscode from "vscode";
import {
  findPredicateOccurrences,
  groupOccurrencesByColor,
} from "./predicateRainbow";

const PALETTE_SIZE = 12;

/** Distinct hues; lightness depends on active color theme kind. */
function paletteColors(kind: vscode.ColorThemeKind): string[] {
  const light =
    kind === vscode.ColorThemeKind.Light ||
    kind === vscode.ColorThemeKind.HighContrastLight;
  const lightness = light ? 38 : 68;
  const saturation = light ? 70 : 65;
  const colors: string[] = [];
  for (let i = 0; i < PALETTE_SIZE; i++) {
    const hue = Math.round((i * 360) / PALETTE_SIZE);
    colors.push(`hsl(${hue} ${saturation}% ${lightness}%)`);
  }
  return colors;
}

export class PredicateRainbow {
  private decorationTypes: vscode.TextEditorDecorationType[] = [];
  private readonly disposables: vscode.Disposable[] = [];
  private enabled = true;

  constructor() {
    this.rebuildDecorationTypes();
    this.disposables.push(
      vscode.window.onDidChangeActiveColorTheme(() => {
        this.rebuildDecorationTypes();
        this.refreshAll();
      }),
      vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor) {
          this.apply(editor);
        }
      }),
      vscode.workspace.onDidChangeTextDocument((event) => {
        const editor = vscode.window.activeTextEditor;
        if (editor && event.document === editor.document) {
          this.apply(editor);
        }
      }),
      vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration("aspls.rainbowPredicates")) {
          this.readConfig();
          this.refreshAll();
        }
      }),
    );
    this.readConfig();
  }

  start(): void {
    this.refreshAll();
  }

  dispose(): void {
    this.clearDecorationTypes();
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables.length = 0;
  }

  private readConfig(): void {
    this.enabled = vscode.workspace
      .getConfiguration("aspls")
      .get<boolean>("rainbowPredicates", true);
  }

  private rebuildDecorationTypes(): void {
    this.clearDecorationTypes();
    const colors = paletteColors(vscode.window.activeColorTheme.kind);
    this.decorationTypes = colors.map((color) =>
      vscode.window.createTextEditorDecorationType({
        // Underline only — leave foreground to LSP semantic role colors.
        textDecoration: `underline solid ${color}`,
      }),
    );
  }

  private clearDecorationTypes(): void {
    for (const dt of this.decorationTypes) {
      dt.dispose();
    }
    this.decorationTypes = [];
  }

  private refreshAll(): void {
    for (const editor of vscode.window.visibleTextEditors) {
      this.apply(editor);
    }
  }

  private apply(editor: vscode.TextEditor): void {
    if (editor.document.languageId !== "asp") {
      return;
    }

    if (!this.enabled || this.decorationTypes.length === 0) {
      for (const dt of this.decorationTypes) {
        editor.setDecorations(dt, []);
      }
      return;
    }

    const occurrences = findPredicateOccurrences(editor.document.getText());
    const groups = groupOccurrencesByColor(occurrences, PALETTE_SIZE);

    for (let i = 0; i < this.decorationTypes.length; i++) {
      const occs = groups.get(i) ?? [];
      const ranges = occs.map(
        (o) =>
          new vscode.Range(
            new vscode.Position(o.line, o.start),
            new vscode.Position(o.line, o.end),
          ),
      );
      editor.setDecorations(this.decorationTypes[i], ranges);
    }
  }
}
