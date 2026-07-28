/**
 * PIN-163 — consolidated B/D stability regression suite.
 * These assertions should fail if known pool/preflight/capability bugs regress.
 */
import * as assert from "assert";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import {
  resolveConfigAdditionalFiles,
  resolvePool,
  shouldWarnDeprecatedAdditionalFilesSetting,
} from "./clingoConfigCore";
import {
  PREFLIGHT_PREFIX,
  preflightClingoRun,
} from "./clingoPreflight";
import { collectBackendCapabilityWarnings } from "./clingoCapabilities";
import { normalizeClingoJson } from "./clingoResultParse";
import { runClingo } from "./clingoRunner";
import type { ClingoRunRequest } from "./clingoTypes";

function baseRequest(overrides: Partial<ClingoRunRequest> = {}): ClingoRunRequest {
  return {
    primaryFile: "/tmp/main.lp",
    program: "a.",
    models: 1,
    additionalFiles: [],
    customArgs: [],
    usePath: false,
    clingoPath: "",
    ...overrides,
  };
}

/** B1: explicit [] is active-only; absent key falls back to discovered. */
function testPoolEmptyArrayRegression(): void {
  const primary = "/proj/main.lp";
  const discovered = [primary, "/proj/other.lp"];
  assert.deepStrictEqual(
    resolvePool({
      primaryFile: primary,
      additionalFiles: [],
      additionalFilesExplicit: true,
      discoveredFiles: discovered,
    }),
    [primary],
  );
  assert.deepStrictEqual(
    resolvePool({
      primaryFile: primary,
      additionalFiles: [],
      additionalFilesExplicit: false,
      discoveredFiles: discovered,
    }),
    discovered,
  );
}

/** B3: settings-only additionalFiles must not drive runtime; warn when config lacks key. */
function testSettingsDeprecationGate(): void {
  assert.strictEqual(
    shouldWarnDeprecatedAdditionalFilesSetting({
      settingsAdditionalFiles: ["facts.lp"],
      configAdditionalFilesDefined: false,
    }),
    true,
  );
  assert.deepStrictEqual(resolveConfigAdditionalFiles(undefined), {
    additionalFiles: [],
    additionalFilesExplicit: false,
  });
  assert.deepStrictEqual(resolveConfigAdditionalFiles([]), {
    additionalFiles: [],
    additionalFilesExplicit: true,
  });
}

/** D1: missing additional file fails before solver with stable prefix. */
function testPreflightMissingFile(): void {
  const missing = path.join(os.tmpdir(), `aspls-bd-missing-${Date.now()}.lp`);
  const outcome = preflightClingoRun(
    baseRequest({ additionalFiles: [missing] }),
  );
  assert.ok(outcome && !outcome.ok);
  assert.ok(outcome!.error.startsWith(PREFLIGHT_PREFIX.missingFile));
  assert.ok(outcome!.commandSummary.includes("WASM"));
}

/** D1: invalid configured PATH fails preflight. */
function testPreflightBadClingoPath(): void {
  const bogus = path.join(os.tmpdir(), `aspls-bd-clingo-${Date.now()}`);
  const outcome = preflightClingoRun(
    baseRequest({ usePath: true, clingoPath: bogus }),
  );
  assert.ok(outcome && !outcome.ok);
  assert.ok(outcome!.error.startsWith(PREFLIGHT_PREFIX.invalidClingoPath));
  assert.strictEqual(outcome!.backend, "path");
}

/** D1: runClingo short-circuits on preflight (no WASM load). */
async function testRunClingoHonoursPreflight(): Promise<void> {
  const missing = path.join(os.tmpdir(), `aspls-bd-runmiss-${Date.now()}.lp`);
  const outcome = await runClingo(
    baseRequest({ additionalFiles: [missing], program: "a." }),
  );
  assert.strictEqual(outcome.ok, false);
  if (outcome.ok) {
    return;
  }
  assert.ok(outcome.error.startsWith(PREFLIGHT_PREFIX.missingFile));
}

/** D2: fragile WASM args produce capability warnings. */
function testFragileWasmWarning(): void {
  const warnings = collectBackendCapabilityWarnings({
    usePath: false,
    customArgs: ["--outf=2", "-q"],
  });
  assert.strictEqual(warnings.length, 1);
  assert.ok(warnings[0].includes("--outf=2"));
  assert.ok(warnings[0].includes("usePath"));
}

/** D: ERROR JSON normalizes to ok:false with message. */
function testErrorNormalization(): void {
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
    "summary",
    "{}",
  );
  assert.strictEqual(outcome.ok, false);
  if (!outcome.ok) {
    assert.match(outcome.error, /grounding stopped/);
    assert.strictEqual(outcome.backend, "wasm");
    assert.strictEqual(outcome.commandSummary, "summary");
  }
}

async function main(): Promise<void> {
  testPoolEmptyArrayRegression();
  testSettingsDeprecationGate();
  testPreflightMissingFile();
  testPreflightBadClingoPath();
  await testRunClingoHonoursPreflight();
  testFragileWasmWarning();
  testErrorNormalization();
  console.log("stabilityBd.regression.test.ts: ok");
}

void main();
