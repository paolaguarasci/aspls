import * as assert from "assert";
import {
  CLINGO_CAPABILITY_MATRIX,
  collectBackendCapabilityWarnings,
  findFragileWasmArgs,
  formatWasmFragileArgsWarning,
  isFragileWasmFlag,
} from "./clingoCapabilities";

function testMatrixHasRows(): void {
  assert.ok(CLINGO_CAPABILITY_MATRIX.length >= 5);
  for (const row of CLINGO_CAPABILITY_MATRIX) {
    assert.ok(row.feature.length > 0);
    assert.ok(["yes", "limited", "no"].includes(row.wasm));
    assert.ok(["yes", "limited", "no"].includes(row.path));
  }
}

function testFragileDetection(): void {
  assert.strictEqual(isFragileWasmFlag("--outf=2"), true);
  assert.strictEqual(isFragileWasmFlag("--const"), false);
  assert.strictEqual(isFragileWasmFlag("-c"), false);
  assert.deepStrictEqual(findFragileWasmArgs(["--const", "n=3"]), []);
  assert.deepStrictEqual(findFragileWasmArgs(["--outf", "2", "-q"]), [
    "--outf",
    "2",
    "-q",
  ]);
  assert.deepStrictEqual(findFragileWasmArgs(["--parallel-mode=2"]), [
    "--parallel-mode=2",
  ]);
}

function testCollectWarnings(): void {
  assert.deepStrictEqual(
    collectBackendCapabilityWarnings({
      usePath: true,
      customArgs: ["--outf=2"],
    }),
    [],
  );
  assert.deepStrictEqual(
    collectBackendCapabilityWarnings({
      usePath: false,
      customArgs: ["--const", "n=1"],
    }),
    [],
  );
  const warnings = collectBackendCapabilityWarnings({
    usePath: false,
    customArgs: ["--stats", "--const", "n=1"],
  });
  assert.strictEqual(warnings.length, 1);
  assert.ok(warnings[0].includes("--stats"));
  assert.ok(warnings[0].includes("aspls.clingo.usePath"));
  assert.ok(formatWasmFragileArgsWarning(["--stats"]).includes("WASM"));
}

function testThreadsSuggestion(): void {
  assert.deepStrictEqual(
    collectBackendCapabilityWarnings({
      usePath: false,
      customArgs: [],
      threads: 1,
    }),
    [],
  );
  assert.deepStrictEqual(
    collectBackendCapabilityWarnings({
      usePath: true,
      customArgs: [],
      threads: 4,
    }),
    [],
  );
  const warnings = collectBackendCapabilityWarnings({
    usePath: false,
    customArgs: [],
    threads: 4,
  });
  assert.strictEqual(warnings.length, 1);
  assert.ok(warnings[0].includes("threads=4"));
  assert.ok(warnings[0].includes("aspls.clingo.usePath"));
}

function testCombinedFragileArgsAndThreads(): void {
  const warnings = collectBackendCapabilityWarnings({
    usePath: false,
    customArgs: ["--outf=2"],
    threads: 2,
  });
  assert.strictEqual(warnings.length, 1);
  assert.ok(warnings[0].includes("--outf=2"));
  assert.ok(warnings[0].includes("threads=2"));
}

function main(): void {
  testMatrixHasRows();
  testFragileDetection();
  testCollectWarnings();
  testThreadsSuggestion();
  testCombinedFragileArgsAndThreads();
  console.log("clingoCapabilities.test.ts: ok");
}

main();
