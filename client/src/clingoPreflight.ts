import * as fs from "fs";
import * as path from "path";
import { collectBackendCapabilityWarnings } from "./clingoCapabilities";
import type {
  ClingoBackend,
  ClingoRunFailure,
  ClingoRunRequest,
} from "./clingoTypes";

/** Stable error prefixes so the Solver panel and notifications stay consistent. */
export const PREFLIGHT_PREFIX = {
  missingFile: "Additional file not found",
  invalidModels: "Invalid models value",
  invalidClingoPath: "Configured Clingo path not found",
} as const;

export function resolveRunBackend(request: ClingoRunRequest): ClingoBackend {
  return request.usePath ? "path" : "wasm";
}

/**
 * Predictable command summary for both success and failure paths.
 * Shows backend, model count, and how many input files will be used.
 */
export function buildPreflightCommandSummary(
  request: ClingoRunRequest,
  opts?: { binary?: string },
): string {
  const fileCount = 1 + request.additionalFiles.length;
  const models =
    request.models === 0 ? "all" : String(request.models);
  if (request.usePath) {
    const binary =
      opts?.binary?.trim() ||
      request.clingoPath.trim() ||
      "clingo";
    return `${binary} · PATH · models=${models} · files=${fileCount}`;
  }
  return `clingo-wasm · WASM · models=${models} · files=${fileCount}`;
}

export function formatMissingAdditionalFilesError(paths: string[]): string {
  const listed = paths.map((p) => `  - ${p}`).join("\n");
  const plural = paths.length === 1 ? "file" : "files";
  return (
    `${PREFLIGHT_PREFIX.missingFile} (${paths.length} ${plural}):\n${listed}\n` +
    "Fix: check paths in aspls.clingo.json `additionalFiles` " +
    "(resolved relative to the active file, then the workspace root)."
  );
}

export function formatInvalidModelsError(models: unknown): string {
  return (
    `${PREFLIGHT_PREFIX.invalidModels}: ${String(models)}. ` +
    "Use 0 for all answer sets, or a non-negative integer."
  );
}

export function formatInvalidClingoPathError(clingoPath: string): string {
  return (
    `${PREFLIGHT_PREFIX.invalidClingoPath}: ${clingoPath}\n` +
    "Fix: set `aspls.clingo.path` to a working Clingo binary, " +
    "or clear it to use `clingo` from PATH, " +
    "or disable `aspls.clingo.usePath` to use the bundled WASM solver."
  );
}

function failure(
  request: ClingoRunRequest,
  error: string,
  opts?: { binary?: string },
): ClingoRunFailure {
  return {
    ok: false,
    backend: resolveRunBackend(request),
    error,
    commandSummary: buildPreflightCommandSummary(request, opts),
  };
}

/**
 * Sync preflight before invoking WASM or PATH Clingo.
 * Returns a standardized failure outcome, or null when the request looks runnable.
 */
export function preflightClingoRun(
  request: ClingoRunRequest,
): ClingoRunFailure | null {
  if (
    typeof request.models !== "number" ||
    !Number.isInteger(request.models) ||
    request.models < 0
  ) {
    return failure(request, formatInvalidModelsError(request.models));
  }

  const missing = request.additionalFiles.filter((file) => !fs.existsSync(file));
  if (missing.length > 0) {
    return failure(request, formatMissingAdditionalFilesError(missing));
  }

  if (request.usePath) {
    const configured = request.clingoPath.trim();
    // Only validate absolute / explicit filesystem paths. Bare names like
    // `clingo` are resolved from PATH later by findClingoBinary.
    if (
      configured &&
      (path.isAbsolute(configured) || configured.includes("/") || configured.includes("\\")) &&
      !fs.existsSync(configured)
    ) {
      return failure(request, formatInvalidClingoPathError(configured), {
        binary: configured,
      });
    }
  }

  return null;
}

/**
 * Non-blocking WASM → PATH suggestions before invoking the solver.
 * Covers fragile customArgs (--outf, --stats, …) and threads > 1.
 */
export function collectPreflightWasmPathSuggestions(
  request: ClingoRunRequest,
): string[] {
  return collectBackendCapabilityWarnings({
    usePath: request.usePath,
    customArgs: request.customArgs,
    threads: request.threads,
  });
}
