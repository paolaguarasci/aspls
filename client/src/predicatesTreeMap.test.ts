import * as assert from "assert";
import { mapDocumentSymbols, mapWorkspaceNodes } from "./predicatesTreeMap";

const range = {
  start: { line: 0, character: 0 },
  end: { line: 0, character: 4 },
};

function testMapDocumentSymbolsNestsRoles(): void {
  const uri = "file:///tmp/x.lp";
  const symbols = [
    {
      name: "bird/1",
      detail: "fact · 1 occ",
      selectionRange: range,
      children: [
        {
          name: "fact",
          detail: "1 occ",
          selectionRange: range,
          children: [
            {
              name: "L1:1",
              selectionRange: range,
            },
          ],
        },
      ],
    },
  ];
  const roots = mapDocumentSymbols(symbols, uri);
  assert.strictEqual(roots.length, 1);
  assert.strictEqual(roots[0].kind, "predicate");
  if (roots[0].kind !== "predicate") return;
  assert.ok(roots[0].children);
  assert.strictEqual(roots[0].children![0].kind, "role");
  assert.strictEqual(roots[0].children![0].children![0].kind, "occurrence");
  assert.strictEqual(roots[0].uri, uri);
  assert.deepStrictEqual(roots[0].range, range);
}

function testMapWorkspaceNodes(): void {
  const nodes = mapWorkspaceNodes([
    {
      name: "bird/1",
      kind: "predicate",
      detail: "fact · 1 occ",
      uri: "file:///tmp/a.lp",
      range,
      children: [
        {
          name: "fact",
          kind: "role",
          detail: "1 occ",
          uri: "file:///tmp/a.lp",
          range,
          children: [
            {
              name: "a.lp:1",
              kind: "occurrence",
              uri: "file:///tmp/a.lp",
              range,
              negated: false,
              children: [],
            },
          ],
        },
      ],
    },
  ]);
  assert.strictEqual(nodes[0].kind, "predicate");
  if (nodes[0].kind !== "predicate") return;
  const role = nodes[0].children![0];
  assert.strictEqual(role.kind, "role");
  if (role.kind !== "role") return;
  assert.strictEqual(role.children![0].label, "a.lp:1");
}

testMapDocumentSymbolsNestsRoles();
testMapWorkspaceNodes();
console.log("predicatesTreeMap.test.ts: ok");
