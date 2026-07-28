/**
 * PIN-163 — minimal WASM vs PATH smoke parity.
 * PATH leg is skipped when Clingo is not installed (CI without native binary).
 */
import * as assert from "assert";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { findClingoBinary, runClingo } from "./clingoRunner";
import type { ClingoRunSuccess } from "./clingoTypes";

function atomSet(outcome: ClingoRunSuccess): Set<string> {
  const atoms = new Set<string>();
  for (const set of outcome.answerSets) {
    for (const a of set.atoms) {
      atoms.add(a);
    }
  }
  return atoms;
}

async function main(): Promise<void> {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "aspls-parity-"));
  const primary = path.join(dir, "smoke.lp");
  const program = "a.\nb :- a.\n";
  fs.writeFileSync(primary, program, "utf8");

  const wasm = await runClingo({
    primaryFile: primary,
    program,
    models: 0,
    additionalFiles: [],
    customArgs: [],
    usePath: false,
    clingoPath: "",
  });
  assert.strictEqual(wasm.ok, true, `WASM smoke failed: ${JSON.stringify(wasm)}`);
  if (!wasm.ok) {
    return;
  }
  assert.strictEqual(wasm.backend, "wasm");
  assert.strictEqual(wasm.result, "SATISFIABLE");
  const wasmAtoms = atomSet(wasm);
  assert.ok(wasmAtoms.has("a"));
  assert.ok(wasmAtoms.has("b"));

  const binary = await findClingoBinary("");
  if (!binary) {
    console.log(
      "clingoRunnerParity.smoke.test.ts: ok (WASM only; PATH skipped — no clingo)",
    );
    return;
  }

  const pathRun = await runClingo({
    primaryFile: primary,
    program,
    models: 0,
    additionalFiles: [],
    customArgs: [],
    usePath: true,
    clingoPath: binary,
  });
  assert.strictEqual(
    pathRun.ok,
    true,
    `PATH smoke failed: ${JSON.stringify(pathRun)}`,
  );
  if (!pathRun.ok) {
    return;
  }
  assert.strictEqual(pathRun.backend, "path");
  assert.strictEqual(pathRun.result, "SATISFIABLE");
  const pathAtoms = atomSet(pathRun);
  assert.deepStrictEqual(
    [...pathAtoms].sort(),
    [...wasmAtoms].sort(),
    "WASM and PATH answer-set atoms should match on the minimal program",
  );
  console.log("clingoRunnerParity.smoke.test.ts: ok (WASM + PATH)");
}

void main();
