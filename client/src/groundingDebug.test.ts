import {
  advanceStepIndex,
  frameAt,
  isSessionFinished,
  parseGroundingDebugPayload,
  type GroundingStep,
  variableEntries,
} from "./groundingDebugCore";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

assert(
  advanceStepIndex([{ kind: "fact", detail: "a(1)" }], -1, "next") === 0,
  "next from -1 starts at 0",
);
assert(
  advanceStepIndex([{ kind: "fact", detail: "a(1)" }], 0, "next") === 1,
  "next advances",
);
assert(
  advanceStepIndex([{ kind: "fact", detail: "a(1)" }], 0, "continue") === 1,
  "continue jumps to end",
);
assert(isSessionFinished(1, 1), "finished when index equals count");
assert(!isSessionFinished(0, 2), "not finished mid session");

const frame = frameAt(
  [
    { kind: "rule", detail: "rule: p(X) :- a(X)" },
    { kind: "fact", detail: "p(1)" },
  ],
  1,
);
assert(frame?.step.kind === "fact", "frameAt returns correct step");

const vars = variableEntries(frame?.step);
assert(vars.some((v) => v.name === "kind" && v.value === "fact"), "variables");

const payload = parseGroundingDebugPayload(
  JSON.stringify({
    ok: true,
    error: null,
    steps: [{ kind: "fact", detail: "q." }],
  }),
);
assert(payload.steps.length === 1, "parse payload");

try {
  parseGroundingDebugPayload(JSON.stringify({ ok: false, error: "boom", steps: [] }));
  assert(false, "should throw on ok=false");
} catch (err) {
  assert(String(err).includes("boom"), "error message propagated");
}

console.log("groundingDebug.test.js: ok");
