import * as crypto from "crypto";
import * as vscode from "vscode";
import {
  PARSER_ERROR_CODE,
  buildTelemetryPayload,
  isParserSyntaxDiagnostic,
  isTelemetryEnabled,
  mergeTelemetryEvents,
  normalizeEndpoint,
  sanitizeFeatureName,
  shouldSendTelemetry,
  type TelemetryEvent,
} from "./telemetryCore";

const INSTALL_ID_KEY = "telemetry.installId";
const FLUSH_INTERVAL_MS = 30_000;
const PARSER_ERROR_COOLDOWN_MS = 60_000;
const MAX_BATCH_SIZE = 50;

type TelemetrySink = (
  endpoint: string,
  body: string,
) => Promise<{ ok: boolean }>;

let queue: TelemetryEvent[] = [];
let flushTimer: ReturnType<typeof setInterval> | undefined;
let lastParserErrorAt = 0;
let enabled = false;
let endpoint = "";
let installId = "";
let extensionVersion = "";
let sink: TelemetrySink = defaultSink;

async function defaultSink(
  target: string,
  body: string,
): Promise<{ ok: boolean }> {
  const response = await fetch(target, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  return { ok: response.ok };
}

function readSettings(): { enabled: boolean; endpoint: string } {
  const cfg = vscode.workspace.getConfiguration("aspls");
  return {
    enabled: isTelemetryEnabled(cfg.get("telemetry.enabled")),
    endpoint: normalizeEndpoint(cfg.get("telemetry.endpoint")),
  };
}

function ensureInstallId(context: vscode.ExtensionContext): string {
  const existing = context.globalState.get<string>(INSTALL_ID_KEY);
  if (existing?.trim()) {
    return existing;
  }
  const created = crypto.randomUUID();
  void context.globalState.update(INSTALL_ID_KEY, created);
  return created;
}

export function trackFeature(feature: string): void {
  if (!enabled) {
    return;
  }
  try {
    queue = mergeTelemetryEvents(queue, [
      {
        kind: "feature_used",
        feature: sanitizeFeatureName(feature),
        ts: Date.now(),
      },
    ], MAX_BATCH_SIZE);
  } catch {
    // Invalid feature names are ignored — telemetry must never break the extension.
  }
}

function trackParserError(): void {
  if (!enabled) {
    return;
  }
  const now = Date.now();
  if (now - lastParserErrorAt < PARSER_ERROR_COOLDOWN_MS) {
    return;
  }
  lastParserErrorAt = now;
  queue = mergeTelemetryEvents(queue, [
    {
      kind: "parser_error",
      category: PARSER_ERROR_CODE,
      ts: now,
    },
  ], MAX_BATCH_SIZE);
}

function hasParserSyntaxError(diagnostics: readonly vscode.Diagnostic[]): boolean {
  return diagnostics.some((diag) =>
    isParserSyntaxDiagnostic(diag.source, diag.code),
  );
}

async function flushQueue(): Promise<void> {
  if (!shouldSendTelemetry(enabled, endpoint) || queue.length === 0) {
    return;
  }
  const batch = queue;
  queue = [];
  try {
    const payload = buildTelemetryPayload(installId, extensionVersion, batch);
    const result = await sink(endpoint, JSON.stringify(payload));
    if (!result.ok) {
      queue = mergeTelemetryEvents(batch, queue, MAX_BATCH_SIZE);
    }
  } catch {
    queue = mergeTelemetryEvents(batch, queue, MAX_BATCH_SIZE);
  }
}

function applySettings(nextEnabled: boolean, nextEndpoint: string): void {
  enabled = nextEnabled;
  endpoint = nextEndpoint;
  if (!enabled) {
    queue = [];
    lastParserErrorAt = 0;
  }
}

/** Test hook — replaces the HTTP sink. */
export function setTelemetrySinkForTests(next: TelemetrySink | undefined): void {
  sink = next ?? defaultSink;
}

export function registerTelemetry(context: vscode.ExtensionContext): void {
  installId = ensureInstallId(context);
  extensionVersion = context.extension.packageJSON.version ?? "0.0.0";
  const initial = readSettings();
  applySettings(initial.enabled, initial.endpoint);

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (
        event.affectsConfiguration("aspls.telemetry.enabled") ||
        event.affectsConfiguration("aspls.telemetry.endpoint")
      ) {
        const next = readSettings();
        applySettings(next.enabled, next.endpoint);
      }
    }),
    vscode.languages.onDidChangeDiagnostics((event) => {
      if (!enabled) {
        return;
      }
      for (const uri of event.uris) {
        const doc = vscode.workspace.textDocuments.find(
          (candidate) => candidate.uri.toString() === uri.toString(),
        );
        if (!doc || doc.languageId !== "asp") {
          continue;
        }
        const diagnostics = vscode.languages.getDiagnostics(uri);
        if (hasParserSyntaxError(diagnostics)) {
          trackParserError();
          break;
        }
      }
    }),
  );

  flushTimer = setInterval(() => {
    void flushQueue();
  }, FLUSH_INTERVAL_MS);
  context.subscriptions.push({
    dispose: () => {
      if (flushTimer) {
        clearInterval(flushTimer);
        flushTimer = undefined;
      }
      void flushQueue();
    },
  });
}
