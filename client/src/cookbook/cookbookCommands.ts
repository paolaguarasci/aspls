import * as vscode from "vscode";
import { COOKBOOK_RECIPES, type CookbookRecipe } from "./recipes";
import { trackFeature } from "../telemetry";

type RecipeQuickPickItem = vscode.QuickPickItem & {
  recipe: CookbookRecipe;
};

type ActionQuickPickItem = vscode.QuickPickItem & {
  action: "insert" | "open";
};

export function registerCookbookCommands(
  context: vscode.ExtensionContext,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("aspls.cookbook.open", () => {
      trackFeature("cookbook.open");
      return openCookbook();
    }),
  );
}

async function openCookbook(): Promise<void> {
  const recipeItems: RecipeQuickPickItem[] = COOKBOOK_RECIPES.map(
    (recipe) => ({
      label: recipe.title,
      description: recipe.category,
      detail: recipe.description,
      recipe,
    }),
  );

  const picked = await vscode.window.showQuickPick(recipeItems, {
    title: "ASP Code Cookbook",
    placeHolder: "Pick a working ASP pattern",
    matchOnDescription: true,
    matchOnDetail: true,
  });
  if (!picked) {
    return;
  }

  const actionItems: ActionQuickPickItem[] = [
    {
      label: "Insert at cursor",
      description: "Paste into the active ASP editor",
      action: "insert",
    },
    {
      label: "Open as new file",
      description: "Open an untitled .lp document",
      action: "open",
    },
  ];

  const action = await vscode.window.showQuickPick(actionItems, {
    title: picked.recipe.title,
    placeHolder: "Insert or open this recipe?",
  });
  if (!action) {
    return;
  }

  if (action.action === "insert") {
    await insertRecipe(picked.recipe);
  } else {
    await openRecipe(picked.recipe);
  }
}

async function insertRecipe(recipe: CookbookRecipe): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "asp") {
    void vscode.window.showErrorMessage(
      "Open an ASP (.lp / .asp) file to insert a cookbook recipe, or choose Open as new file.",
    );
    return;
  }

  const text =
    editor.selection.isEmpty && editor.selection.active.character > 0
      ? `\n${recipe.code}`
      : recipe.code;

  const ok = await editor.edit((editBuilder) => {
    editBuilder.insert(editor.selection.active, text);
  });
  if (!ok) {
    void vscode.window.showErrorMessage("Failed to insert cookbook recipe.");
  }
}

async function openRecipe(recipe: CookbookRecipe): Promise<void> {
  const doc = await vscode.workspace.openTextDocument({
    content: recipe.code,
    language: "asp",
  });
  await vscode.window.showTextDocument(doc);
}
