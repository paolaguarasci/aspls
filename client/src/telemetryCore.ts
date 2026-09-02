export const PARSER_ERROR_CODE = "parser.syntax";

export type FeatureUsedEvent = {
  kind: "feature_used";
  feature: string;
  ts: number;
};

export type ParserErrorEvent = {
  kind: "parser_error";
  category: string;
  ts: number;
};

export type TelemetryEvent = FeatureUsedEvent | ParserErrorEvent;

export type TelemetryPayload = {
  installId: string;
  extensionVersion: string;
  events: TelemetryEvent[];
};

const FEATURE_PATTERN = /^[a-z][a-z0-9._-]{0,63}$/;

export function isTelemetryEnabled(enabled: unknown): boolean {
  return enabled === true;
}

export function normalizeEndpoint(endpoint: unknown): string {
  if (typeof endpoint !== "string") {
    return "";
  }
  return endpoint.trim();
}

export function shouldSendTelemetry(
  enabled: unknown,
  endpoint: unknown,
): boolean {
  return isTelemetryEnabled(enabled) && normalizeEndpoint(endpoint).length > 0;
}

export function sanitizeFeatureName(feature: string): string {
  const normalized = feature.trim().toLowerCase();
  if (!FEATURE_PATTERN.test(normalized)) {
    throw new Error(`Invalid telemetry feature name: ${feature}`);
  }
  return normalized;
}

export function isParserSyntaxDiagnostic(
  source: string | undefined,
  code: string | number | { value: string | number } | undefined,
): boolean {
  if (source !== "aspls") {
    return false;
  }
  if (code === PARSER_ERROR_CODE) {
    return true;
  }
  if (typeof code === "object" && code !== null && "value" in code) {
    return code.value === PARSER_ERROR_CODE;
  }
  return false;
}

export function buildTelemetryPayload(
  installId: string,
  extensionVersion: string,
  events: TelemetryEvent[],
): TelemetryPayload {
  if (!installId.trim()) {
    throw new Error("installId is required");
  }
  if (!extensionVersion.trim()) {
    throw new Error("extensionVersion is required");
  }
  return {
    installId,
    extensionVersion,
    events: [...events],
  };
}

export function mergeTelemetryEvents(
  existing: TelemetryEvent[],
  incoming: TelemetryEvent[],
  maxBatchSize: number,
): TelemetryEvent[] {
  if (maxBatchSize <= 0) {
    throw new Error("maxBatchSize must be positive");
  }
  return [...existing, ...incoming].slice(-maxBatchSize);
}
