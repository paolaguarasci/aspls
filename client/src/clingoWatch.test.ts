import * as assert from "assert";
import * as path from "path";
import {
  buildWatchPool,
  normalizeWatchDebounceMs,
  shouldWatchRerun,
} from "./clingoWatchCore";

function testShouldWatchRerun(): void {
  const primary = path.join("/proj", "main.lp");
  const extra = path.join("/proj", "facts.lp");
  const pool = buildWatchPool(primary, [extra]);

  assert.strictEqual(
    shouldWatchRerun(true, primary, primary, pool),
    true,
  );
  assert.strictEqual(
    shouldWatchRerun(true, primary, extra, pool),
    true,
  );
  assert.strictEqual(
    shouldWatchRerun(false, primary, primary, pool),
    false,
  );
  assert.strictEqual(
    shouldWatchRerun(true, undefined, primary, pool),
    false,
  );
  assert.strictEqual(
    shouldWatchRerun(true, primary, path.join("/proj", "other.lp"), pool),
    false,
  );
}

function testBuildWatchPool(): void {
  const primary = path.join("/proj", "main.lp");
  const pool = buildWatchPool(primary, [
    path.join("/proj", "facts.lp"),
    primary,
  ]);
  assert.strictEqual(pool.length, 2);
  assert.ok(pool.includes(primary));
  assert.ok(pool.includes(path.join("/proj", "facts.lp")));
}

function testNormalizeWatchDebounceMs(): void {
  assert.strictEqual(normalizeWatchDebounceMs(300), 300);
  assert.strictEqual(normalizeWatchDebounceMs(0), 0);
  assert.strictEqual(normalizeWatchDebounceMs(-1), 500);
  assert.strictEqual(normalizeWatchDebounceMs("200"), 500);
  assert.strictEqual(normalizeWatchDebounceMs(NaN), 500);
}

function run(): void {
  testShouldWatchRerun();
  testBuildWatchPool();
  testNormalizeWatchDebounceMs();
  console.log("clingoWatch.test.ts: ok");
}

run();
