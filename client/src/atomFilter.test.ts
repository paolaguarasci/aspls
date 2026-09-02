import * as assert from "assert";
import { atomMatchesFilter, filterAtoms } from "./atomFilter";

function testEmptyQueryMatchesAll(): void {
  assert.strictEqual(atomMatchesFilter("flies(tweety)", ""), true);
  assert.strictEqual(atomMatchesFilter("flies(tweety)", "   "), true);
  assert.deepStrictEqual(
    filterAtoms(["a", "b", "c"], ""),
    ["a", "b", "c"],
  );
}

function testCaseInsensitiveSubstring(): void {
  assert.strictEqual(atomMatchesFilter("flies(tweety)", "FLIES"), true);
  assert.strictEqual(atomMatchesFilter("bird(tweety)", "TWEETY"), true);
  assert.strictEqual(atomMatchesFilter("flies(tweety)", "cat"), false);
}

function testFilterAtoms(): void {
  assert.deepStrictEqual(
    filterAtoms(["flies(tweety)", "bird(tweety)", "cat(mia)"], "tweety"),
    ["flies(tweety)", "bird(tweety)"],
  );
  assert.deepStrictEqual(filterAtoms(["a", "b"], "z"), []);
}

testEmptyQueryMatchesAll();
testCaseInsensitiveSubstring();
testFilterAtoms();
console.log("atomFilter tests passed");
