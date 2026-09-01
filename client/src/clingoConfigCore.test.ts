import * as assert from "assert";
import * as path from "path";
import {
  asConstantsArray,
  asStringArray,
  buildClingoCustomArgs,
  constantsToArgv,
  dedupePaths,
  isValidModels,
  mergeClingoFileConfig,
  removePathEntry,
  resolveConfigAdditionalFiles,
  resolvePool,
  shouldWarnDeprecatedAdditionalFilesSetting,
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
    constants: [],
    additionalFiles: ["a.lp"],
  };
  const merged = mergeClingoFileConfig(base, {
    models: 5,
    additionalFiles: ["b.lp"],
    constants: [{ name: "n", value: "3" }],
  });
  assert.strictEqual(merged.models, 5);
  assert.deepStrictEqual(merged.additionalFiles, ["b.lp"]);
  assert.deepStrictEqual(merged.constants, [{ name: "n", value: "3" }]);
  assert.strictEqual(merged.threads, 1);
  assert.strictEqual(merged.customArgs, "");
}

function testConstantsHelpers(): void {
  assert.deepStrictEqual(
    constantsToArgv([
      { name: "n", value: "3" },
      { name: "width", value: "2" },
    ]),
    ["-c", "n=3", "-c", "width=2"],
  );
  assert.deepStrictEqual(constantsToArgv([{ name: "  ", value: "1" }]), []);
  assert.deepStrictEqual(
    buildClingoCustomArgs({
      constants: [{ name: "n", value: "1" }],
      customArgs: "--stats",
    }),
    ["-c", "n=1", "--stats"],
  );
  assert.deepStrictEqual(
    asConstantsArray([
      { name: "n", value: "3" },
      { name: 1, value: "x" },
      null,
    ]),
    [{ name: "n", value: "3" }],
  );
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

function testResolvePool(): void {
  const primary = "/proj/main.lp";
  const discovered = ["/proj/main.lp", "/proj/other.lp"];

  // additionalFiles absent → full workspace fallback
  assert.deepStrictEqual(
    resolvePool({
      primaryFile: primary,
      additionalFiles: [],
      additionalFilesExplicit: false,
      discoveredFiles: discovered,
    }),
    discovered,
  );

  // additionalFiles=[] (explicit empty) → active file only (regression PIN-164)
  assert.deepStrictEqual(
    resolvePool({
      primaryFile: primary,
      additionalFiles: [],
      additionalFilesExplicit: true,
      discoveredFiles: discovered,
    }),
    [primary],
  );

  // additionalFiles non-empty → active + entries (deduped)
  assert.deepStrictEqual(
    resolvePool({
      primaryFile: primary,
      additionalFiles: ["/proj/facts.lp", primary],
      additionalFilesExplicit: true,
      discoveredFiles: discovered,
    }),
    [primary, "/proj/facts.lp"],
  );
}

function testResolveConfigAdditionalFiles(): void {
  assert.deepStrictEqual(resolveConfigAdditionalFiles(undefined), {
    additionalFiles: [],
    additionalFilesExplicit: false,
  });
  assert.deepStrictEqual(resolveConfigAdditionalFiles([]), {
    additionalFiles: [],
    additionalFilesExplicit: true,
  });
  assert.deepStrictEqual(resolveConfigAdditionalFiles(["a.lp", 1, "b.lp"]), {
    additionalFiles: ["a.lp", "b.lp"],
    additionalFilesExplicit: true,
  });
}

function testShouldWarnDeprecatedAdditionalFilesSetting(): void {
  assert.strictEqual(
    shouldWarnDeprecatedAdditionalFilesSetting({
      settingsAdditionalFiles: ["facts.lp"],
      configAdditionalFilesDefined: false,
    }),
    true,
  );
  assert.strictEqual(
    shouldWarnDeprecatedAdditionalFilesSetting({
      settingsAdditionalFiles: ["facts.lp"],
      configAdditionalFilesDefined: true,
    }),
    false,
  );
  assert.strictEqual(
    shouldWarnDeprecatedAdditionalFilesSetting({
      settingsAdditionalFiles: [],
      configAdditionalFilesDefined: false,
    }),
    false,
  );
}

function testAsStringArray(): void {
  assert.deepStrictEqual(asStringArray(["a", 1, "b"]), ["a", "b"]);
  assert.deepStrictEqual(asStringArray(null), []);
}

function main(): void {
  testIsValidModels();
  testMergeClingoFileConfig();
  testConstantsHelpers();
  testToWorkspaceRelativePath();
  testDedupeAndRemove();
  testResolvePool();
  testResolveConfigAdditionalFiles();
  testShouldWarnDeprecatedAdditionalFilesSetting();
  testAsStringArray();
  console.log("clingoConfigCore.test.ts: ok");
}

main();
