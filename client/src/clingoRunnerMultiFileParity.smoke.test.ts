/**
 * ASPLS-34 — WASM vs PATH smoke parity on a multi-file program
 * (additionalFiles concatenation under WASM vs separate CLI args under PATH).
 * PATH leg skipped when Clingo is not installed.
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
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "aspls-multifile-"));
  const facts = path.join(dir, "facts.lp");
  const rules = path.join(dir, "rules.lp");
  fs.writeFileSync(
    facts,
    "bird(tweety).\nbird(pingu).\npenguin(pingu).\n",
    "utf8",
  );
  const rulesProgram = "flies(X) :- bird(X), not penguin(X).\n#show flies/1.\n";
  fs.writeFileSync(rules, rulesProgram, "utf8");

  const wasm = await runClingo({
    primaryFile: rules,
    program: rulesProgram,
    models: 0,
    additionalFiles: [facts],
    customArgs: [],
    usePath: false,
    clingoPath: "",
  });
  assert.strictEqual(
    wasm.ok,
    true,
    `WASM multi-file smoke failed: ${JSON.stringify(wasm)}`,
  );
  if (!wasm.ok) {
    return;
  }
  assert.strictEqual(wasm.backend, "wasm");
  assert.strictEqual(wasm.result, "SATISFIABLE");
  const wasmAtoms = atomSet(wasm);
  assert.ok(wasmAtoms.has("flies(tweety)"));
  assert.ok(!wasmAtoms.has("flies(pingu)"));

  const binary = await findClingoBinary("");
  if (!binary) {
    console.log(
      "clingoRunnerMultiFileParity.smoke.test.ts: ok (WASM only; PATH skipped — no clingo)",
    );
    return;
  }

  const pathRun = await runClingo({
    primaryFile: rules,
    program: rulesProgram,
    models: 0,
    additionalFiles: [facts],
    customArgs: [],
    usePath: true,
    clingoPath: binary,
  });
  assert.strictEqual(
    pathRun.ok,
    true,
    `PATH multi-file smoke failed: ${JSON.stringify(pathRun)}`,
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
    "WASM concatenation and PATH separate files should yield the same atoms",
  );
  console.log("clingoRunnerMultiFileParity.smoke.test.ts: ok (WASM + PATH)");
}

void main();
