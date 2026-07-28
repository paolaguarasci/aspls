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

function main(): void {
  testMatrixHasRows();
  testFragileDetection();
  testCollectWarnings();
  console.log("clingoCapabilities.test.ts: ok");
}

main();
