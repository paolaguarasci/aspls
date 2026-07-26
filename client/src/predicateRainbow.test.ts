import * as assert from "assert";
import {
  colorIndexForPredicate,
  findPredicateOccurrences,
  groupOccurrencesByColor,
} from "./predicateRainbow";

function namesIn(text: string): string[] {
  return findPredicateOccurrences(text).map((o) => o.name);
}

function testFindSkipsCommentsNotAndHashDirectives(): void {
  const text = [
    "% cell should be ignored",
    "cell(X) :- size(N), not forbidden(X).",
    "#show cell/1.",
    "n = #count{ X : cell(X) }.",
  ].join("\n");

  assert.deepStrictEqual(namesIn(text), [
    "cell",
    "size",
    "forbidden",
    "cell",
    "cell",
  ]);
}

function testSkipsConstantsInsideTermsAndConstDirective(): void {
  const text = [
    "#const n = 5.",
    "domain(1..n).",
    "label(hello).",
    "edge(a, b).",
    "cell(Y) :- Y = 1..width.",
    "ok :- X <= n.",
    "ok.",
    "alarm :- danger, not silenced.",
  ].join("\n");

  assert.deepStrictEqual(namesIn(text), [
    "domain",
    "label",
    "edge",
    "cell",
    "ok",
    "ok",
    "alarm",
    "danger",
    "silenced",
  ]);
}

function testSamePredicateSameColor(): void {
  assert.strictEqual(
    colorIndexForPredicate("cell", 12),
    colorIndexForPredicate("cell", 12),
  );
  assert.notStrictEqual(
    colorIndexForPredicate("very_unique_pred_alpha", 64),
    colorIndexForPredicate("very_unique_pred_beta", 64),
  );
}

function testGroupByColor(): void {
  const occ = findPredicateOccurrences("a. b. a.");
  const groups = groupOccurrencesByColor(occ, 12);
  const aIndex = colorIndexForPredicate("a", 12);
  assert.strictEqual(groups.get(aIndex)?.length, 2);
}

testFindSkipsCommentsNotAndHashDirectives();
testSkipsConstantsInsideTermsAndConstDirective();
testSamePredicateSameColor();
testGroupByColor();
console.log("predicateRainbow tests passed");
