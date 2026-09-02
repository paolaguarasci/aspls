import * as assert from "assert";
import { diffAtomSets } from "./answerSetDiff";

function testIdenticalSets(): void {
  assert.deepStrictEqual(diffAtomSets(["a", "b"], ["a", "b"]), {
    added: [],
    removed: [],
    unchanged: ["a", "b"],
  });
}

function testAddedAndRemoved(): void {
  assert.deepStrictEqual(diffAtomSets(["a", "b"], ["b", "c"]), {
    added: ["c"],
    removed: ["a"],
    unchanged: ["b"],
  });
}

function testEmptyPrevious(): void {
  assert.deepStrictEqual(diffAtomSets([], ["a", "b"]), {
    added: ["a", "b"],
    removed: [],
    unchanged: [],
  });
}

function testEmptyCurrent(): void {
  assert.deepStrictEqual(diffAtomSets(["a", "b"], []), {
    added: [],
    removed: ["a", "b"],
    unchanged: [],
  });
}

function testBothEmpty(): void {
  assert.deepStrictEqual(diffAtomSets([], []), {
    added: [],
    removed: [],
    unchanged: [],
  });
}

testIdenticalSets();
testAddedAndRemoved();
testEmptyPrevious();
testEmptyCurrent();
testBothEmpty();
console.log("answerSetDiff tests passed");
