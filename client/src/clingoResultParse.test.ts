import { splitCustomArgs } from "./clingoConfigCore";
import {
  normalizeClingoJson,
  parseClingoJsonStdout,
} from "./clingoResultParse";
import * as assert from "assert";

function testSplitCustomArgs(): void {
  assert.deepStrictEqual(splitCustomArgs(""), []);
  assert.deepStrictEqual(splitCustomArgs("  --verbose  -q  "), [
    "--verbose",
    "-q",
  ]);
  assert.deepStrictEqual(splitCustomArgs('--const n=3 "hello world"'), [
    "--const",
    "n=3",
    "hello world",
  ]);
}

function testNormalizeSatisfiable(): void {
  const outcome = normalizeClingoJson(
    {
      Solver: "clingo version 5.8.0",
      Result: "SATISFIABLE",
      Calls: 1,
      Call: [
        {
          Witnesses: [{ Value: ["a", "b"] }, { Value: ["c"] }],
        },
      ],
      Models: { Number: 2, More: "no" },
      Time: { Total: 0.01 },
      Warnings: [""],
    },
    "wasm",
    "clingo-wasm",
    "{}",
  );
  assert.strictEqual(outcome.ok, true);
  if (!outcome.ok) {
    return;
  }
  assert.strictEqual(outcome.result, "SATISFIABLE");
  assert.strictEqual(outcome.answerSets.length, 2);
  assert.deepStrictEqual(outcome.answerSets[0].atoms, ["a", "b"]);
  assert.deepStrictEqual(outcome.answerSets[1].atoms, ["c"]);
  assert.strictEqual(outcome.warnings.length, 0);
}

function testNormalizeError(): void {
  const outcome = normalizeClingoJson(
    {
      Result: "ERROR",
      Error: "grounding stopped because of errors",
      Calls: 0,
      Call: [],
      Models: { Number: 0, More: "no" },
      Time: { Total: 0 },
    },
    "wasm",
    "clingo-wasm",
    "{}",
  );
  assert.strictEqual(outcome.ok, false);
  if (outcome.ok) {
    return;
  }
  assert.match(outcome.error, /grounding stopped/);
}

function testParseStdoutWithStderrWarnings(): void {
  const stdout = JSON.stringify({
    Result: "SATISFIABLE",
    Calls: 1,
    Call: [{ Witnesses: [{ Value: ["a"] }] }],
    Models: { Number: 1, More: "no" },
    Time: { Total: 0, CPU: 0, Model: 0, Solve: 0, Unsat: 0 },
  });
  const outcome = parseClingoJsonStdout(
    stdout,
    "file.lp:1:1-2: info: atom does not occur in any rule head:\n  b\n",
    "path",
    "clingo file.lp 1 --outf=2",
    10,
  );
  assert.strictEqual(outcome.ok, true);
  if (!outcome.ok) {
    return;
  }
  assert.ok(outcome.warnings.some((w) => w.includes("atom does not occur")));
}

function testNormalizeStats(): void {
  const outcome = normalizeClingoJson(
    {
      Result: "SATISFIABLE",
      Calls: 1,
      Call: [{ Witnesses: [{ Value: ["a"] }] }],
      Models: { Number: 1, More: "no" },
      Time: { Total: 0.012, Solve: 0.006 },
      Stats: { LP: { Atoms: 200 } },
    },
    "path",
    "clingo file.lp 1 --outf=2 --stats",
    "{}",
  );
  assert.strictEqual(outcome.ok, true);
  if (!outcome.ok) {
    return;
  }
  assert.strictEqual(outcome.timeTotal, 0.012);
  assert.strictEqual(outcome.timeSolve, 0.006);
  assert.strictEqual(outcome.timeGrounding, 0.006);
  assert.strictEqual(outcome.atomCount, 200);
}

function testParseUnsat(): void {
  const stdout = JSON.stringify({
    Result: "UNSATISFIABLE",
    Calls: 1,
    Call: [{ Witnesses: [] }],
    Models: { Number: 0, More: "no" },
    Time: { Total: 0, CPU: 0, Model: 0, Solve: 0, Unsat: 0 },
  });
  const outcome = parseClingoJsonStdout(
    stdout,
    "",
    "path",
    "clingo",
    20,
  );
  assert.strictEqual(outcome.ok, true);
  if (!outcome.ok) {
    return;
  }
  assert.strictEqual(outcome.result, "UNSATISFIABLE");
  assert.strictEqual(outcome.answerSets.length, 0);
}

testSplitCustomArgs();
testNormalizeSatisfiable();
testNormalizeError();
testNormalizeStats();
testParseStdoutWithStderrWarnings();
testParseUnsat();
console.log("clingoResultParse / clingoConfig tests passed");
