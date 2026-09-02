import * as assert from "assert";
import {
  PARSER_ERROR_CODE,
  buildTelemetryPayload,
  isParserSyntaxDiagnostic,
  isTelemetryEnabled,
  mergeTelemetryEvents,
  sanitizeFeatureName,
  shouldSendTelemetry,
  type TelemetryEvent,
} from "./telemetryCore";

function testOptInGating(): void {
  assert.strictEqual(isTelemetryEnabled(false), false);
  assert.strictEqual(isTelemetryEnabled(true), true);
  assert.strictEqual(isTelemetryEnabled(undefined), false);
  assert.strictEqual(shouldSendTelemetry(false, "https://example.com"), false);
  assert.strictEqual(shouldSendTelemetry(true, ""), false);
  assert.strictEqual(shouldSendTelemetry(true, "  "), false);
  assert.strictEqual(
    shouldSendTelemetry(true, "https://example.com/events"),
    true,
  );
}

function testSanitizeFeatureName(): void {
  assert.strictEqual(sanitizeFeatureName("clingo.computeFirst"), "clingo.computefirst");
  assert.throws(() => sanitizeFeatureName("../secret"));
  assert.throws(() => sanitizeFeatureName(""));
}

function testParserDiagnosticFilter(): void {
  assert.strictEqual(
    isParserSyntaxDiagnostic("aspls", PARSER_ERROR_CODE),
    true,
  );
  assert.strictEqual(
    isParserSyntaxDiagnostic("aspls", { value: PARSER_ERROR_CODE }),
    true,
  );
  assert.strictEqual(
    isParserSyntaxDiagnostic("aspls (clingo)", PARSER_ERROR_CODE),
    false,
  );
  assert.strictEqual(
    isParserSyntaxDiagnostic("aspls", "learner.ruleOrder"),
    false,
  );
}

function testAnonymousPayload(): void {
  const events: TelemetryEvent[] = [
    { kind: "feature_used", feature: "clingo.computefirst", ts: 1 },
    { kind: "parser_error", category: PARSER_ERROR_CODE, ts: 2 },
  ];
  const payload = buildTelemetryPayload(
    "11111111-1111-4111-8111-111111111111",
    "0.6.0",
    events,
  );
  assert.deepStrictEqual(Object.keys(payload).sort(), [
    "events",
    "extensionVersion",
    "installId",
  ]);
  assert.strictEqual(payload.events.length, 2);
  assert.strictEqual(payload.events[0].kind, "feature_used");
  assert.strictEqual(payload.events[1].kind, "parser_error");
  if (payload.events[1].kind === "parser_error") {
    assert.strictEqual(payload.events[1].category, PARSER_ERROR_CODE);
  }
  for (const event of payload.events) {
    assert.ok(!("message" in event));
    assert.ok(!("path" in event));
    assert.ok(!("uri" in event));
  }
}

function testMergeTelemetryEvents(): void {
  const a: TelemetryEvent[] = [
    { kind: "feature_used", feature: "cookbook.open", ts: 1 },
  ];
  const b: TelemetryEvent[] = [
    { kind: "parser_error", category: PARSER_ERROR_CODE, ts: 2 },
  ];
  assert.deepStrictEqual(mergeTelemetryEvents(a, b, 10), [...a, ...b]);
  assert.deepStrictEqual(mergeTelemetryEvents(a, b, 1), [b[0]]);
}

function run(): void {
  testOptInGating();
  testSanitizeFeatureName();
  testParserDiagnosticFilter();
  testAnonymousPayload();
  testMergeTelemetryEvents();
  console.log("telemetry.test.ts: ok");
}

void run();
