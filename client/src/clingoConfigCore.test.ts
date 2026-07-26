import * as assert from "assert";
import * as path from "path";
import {
  dedupePaths,
  isValidModels,
  mergeClingoFileConfig,
  removePathEntry,
  toWorkspaceRelativePath,
} from "./clingoConfigCore";

function testIsValidModels(): void {
  assert.strictEqual(isValidModels(0), true);
  assert.strictEqual(isValidModels(3), true);
  assert.strictEqual(isValidModels(-1), false);
  assert.strictEqual(isValidModels(1.5), false);
  assert.strictEqual(isValidModels("2"), false);
  assert.strictEqual(isValidModels(NaN), false);
}

function testMergeClingoFileConfig(): void {
  const base = {
    models: 0,
    threads: 1,
    customArgs: "",
    additionalFiles: ["a.lp"],
  };
  const merged = mergeClingoFileConfig(base, {
    models: 5,
    additionalFiles: ["b.lp"],
  });
  assert.strictEqual(merged.models, 5);
  assert.deepStrictEqual(merged.additionalFiles, ["b.lp"]);
  assert.strictEqual(merged.threads, 1);
  assert.strictEqual(merged.customArgs, "");
}

function testToWorkspaceRelativePath(): void {
  const root = path.join("/tmp", "ws");
  const inside = path.join(root, "dir", "x.lp");
  assert.strictEqual(
    toWorkspaceRelativePath(inside, root),
    path.join("dir", "x.lp"),
  );
  assert.strictEqual(
    toWorkspaceRelativePath("/elsewhere/y.lp", root),
    "/elsewhere/y.lp",
  );
}

function testDedupeAndRemove(): void {
  assert.deepStrictEqual(dedupePaths(["a.lp", "b.lp", "a.lp"]), [
    "a.lp",
    "b.lp",
  ]);
  assert.deepStrictEqual(removePathEntry(["a.lp", "b.lp"], "a.lp"), ["b.lp"]);
  assert.deepStrictEqual(removePathEntry(["a.lp"], "missing.lp"), ["a.lp"]);
}

function main(): void {
  testIsValidModels();
  testMergeClingoFileConfig();
  testToWorkspaceRelativePath();
  testDedupeAndRemove();
  console.log("clingoConfigCore.test.ts: ok");
}

main();
