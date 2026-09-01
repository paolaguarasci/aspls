import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { test } from "node:test";
import {
  collectIncludedFiles,
  expandIncludesInProgram,
  extractIncludes,
} from "./clingoIncludes.js";

test("extractIncludes returns quoted paths", () => {
  assert.deepEqual(extractIncludes('#include "facts.lp".\nbird(a).'), [
    "facts.lp",
  ]);
});

test("expandIncludesInProgram inlines included content", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "aspls-include-"));
  const facts = path.join(dir, "facts.lp");
  const main = path.join(dir, "main.lp");
  fs.writeFileSync(facts, "bird(tweety).\n", "utf8");
  fs.writeFileSync(
    main,
    '#include "facts.lp".\nok :- bird(X).\n',
    "utf8",
  );
  const expanded = expandIncludesInProgram(main, fs.readFileSync(main, "utf8"), dir);
  assert.ok(expanded.includes("bird(tweety)."));
  assert.ok(expanded.includes("ok :- bird(X)."));
  assert.ok(!expanded.includes("#include"));
});

test("collectIncludedFiles is transitive", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "aspls-include-"));
  fs.writeFileSync(path.join(dir, "c.lp"), "base(y).\n", "utf8");
  fs.writeFileSync(path.join(dir, "b.lp"), '#include "c.lp".\n', "utf8");
  fs.writeFileSync(path.join(dir, "a.lp"), '#include "b.lp".\n', "utf8");
  const files = collectIncludedFiles(
    path.join(dir, "a.lp"),
    fs.readFileSync(path.join(dir, "a.lp"), "utf8"),
    dir,
  );
  assert.deepEqual(files.sort(), [
    path.join(dir, "b.lp"),
    path.join(dir, "c.lp"),
  ].sort());
});
