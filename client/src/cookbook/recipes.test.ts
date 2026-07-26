import * as assert from "assert";
import { COOKBOOK_RECIPES } from "./recipes";

function testCatalogNonEmpty(): void {
  assert.ok(COOKBOOK_RECIPES.length >= 8);
}

function testUniqueIds(): void {
  const ids = COOKBOOK_RECIPES.map((r) => r.id);
  assert.strictEqual(ids.length, new Set(ids).size);
}

function testRecipesHaveWorkingCode(): void {
  for (const recipe of COOKBOOK_RECIPES) {
    assert.ok(recipe.title.length > 0, `${recipe.id}: empty title`);
    assert.ok(recipe.category.length > 0, `${recipe.id}: empty category`);
    assert.ok(recipe.description.length > 0, `${recipe.id}: empty description`);
    assert.ok(recipe.code.trim().length > 0, `${recipe.id}: empty code`);
    const looksComplete =
      recipe.code.includes("#") ||
      recipe.code.includes(":~") ||
      /.\s*$/m.test(recipe.code.trim());
    assert.ok(
      looksComplete,
      `${recipe.id}: code should be a working fragment (directive, weak constraint, or statements ending with .)`,
    );
    // Prefer statements that end with a period (ASP statements / directives)
    assert.ok(
      recipe.code.trim().endsWith(".") ||
        recipe.code.includes("#") ||
        recipe.code.includes(":~"),
      `${recipe.id}: expected terminating . or # / :~`,
    );
  }
}

testCatalogNonEmpty();
testUniqueIds();
testRecipesHaveWorkingCode();
console.log("cookbook recipes tests passed");
