import * as assert from "assert";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import {
  PREFLIGHT_PREFIX,
  buildPreflightCommandSummary,
  formatInvalidClingoPathError,
  formatInvalidModelsError,
  formatMissingAdditionalFilesError,
  preflightClingoRun,
  resolveRunBackend,
} from "./clingoPreflight";
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

function testResolveBackend(): void {
  assert.strictEqual(resolveRunBackend(baseRequest({ usePath: false })), "wasm");
  assert.strictEqual(resolveRunBackend(baseRequest({ usePath: true })), "path");
}

function testCommandSummary(): void {
  assert.strictEqual(
    buildPreflightCommandSummary(
      baseRequest({ models: 0, additionalFiles: ["/a.lp", "/b.lp"] }),
    ),
    "clingo-wasm · WASM · models=all · files=3",
  );
  assert.strictEqual(
    buildPreflightCommandSummary(
      baseRequest({
        usePath: true,
        clingoPath: "/usr/bin/clingo",
        models: 2,
      }),
    ),
    "/usr/bin/clingo · PATH · models=2 · files=1",
  );
}

function testMissingAdditionalFile(): void {
  const missing = path.join(os.tmpdir(), `aspls-missing-${Date.now()}.lp`);
  const outcome = preflightClingoRun(
    baseRequest({ additionalFiles: [missing] }),
  );
  assert.ok(outcome);
  assert.strictEqual(outcome!.ok, false);
  assert.strictEqual(outcome!.backend, "wasm");
  assert.ok(outcome!.error.startsWith(PREFLIGHT_PREFIX.missingFile));
  assert.ok(outcome!.error.includes(missing));
  assert.ok(outcome!.error.includes("aspls.clingo.json"));
  assert.ok(outcome!.commandSummary.includes("WASM"));
}

function testExistingAdditionalFilePasses(): void {
  const existing = path.join(os.tmpdir(), `aspls-exists-${Date.now()}.lp`);
  fs.writeFileSync(existing, "b.\n", "utf8");
  try {
    const outcome = preflightClingoRun(
      baseRequest({ additionalFiles: [existing] }),
    );
    assert.strictEqual(outcome, null);
  } finally {
    fs.unlinkSync(existing);
  }
}

function testInvalidModels(): void {
  const outcome = preflightClingoRun(baseRequest({ models: -1 }));
  assert.ok(outcome);
  assert.ok(outcome!.error.startsWith(PREFLIGHT_PREFIX.invalidModels));
  assert.strictEqual(
    formatInvalidModelsError(-1).startsWith(PREFLIGHT_PREFIX.invalidModels),
    true,
  );
}

function testInvalidConfiguredPath(): void {
  const bogus = path.join(os.tmpdir(), `aspls-no-clingo-${Date.now()}`);
  const outcome = preflightClingoRun(
    baseRequest({
      usePath: true,
      clingoPath: bogus,
    }),
  );
  assert.ok(outcome);
  assert.strictEqual(outcome!.backend, "path");
  assert.ok(outcome!.error.startsWith(PREFLIGHT_PREFIX.invalidClingoPath));
  assert.ok(outcome!.error.includes(bogus));
  assert.ok(outcome!.commandSummary.includes("PATH"));
  assert.ok(
    formatInvalidClingoPathError(bogus).includes(PREFLIGHT_PREFIX.invalidClingoPath),
  );
}

function testEmptyConfiguredPathSkipsPathExistsCheck(): void {
  // Binary discovery happens later in the PATH runner; preflight must not fail
  // when clingoPath is empty or a bare command name (looked up on PATH).
  assert.strictEqual(
    preflightClingoRun(baseRequest({ usePath: true, clingoPath: "" })),
    null,
  );
  assert.strictEqual(
    preflightClingoRun(baseRequest({ usePath: true, clingoPath: "clingo" })),
    null,
  );
}

function testFormatMissingHelpers(): void {
  const msg = formatMissingAdditionalFilesError(["/a.lp", "/b.lp"]);
  assert.ok(msg.includes("2 files"));
  assert.ok(msg.includes("/a.lp"));
  assert.ok(msg.includes("/b.lp"));
}

function main(): void {
  testResolveBackend();
  testCommandSummary();
  testMissingAdditionalFile();
  testExistingAdditionalFilePasses();
  testInvalidModels();
  testInvalidConfiguredPath();
  testEmptyConfiguredPathSkipsPathExistsCheck();
  testFormatMissingHelpers();
  console.log("clingoPreflight.test.ts: ok");
}

main();
