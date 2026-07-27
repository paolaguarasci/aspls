import * as path from "path";

/** Split a Clingo custom-args string into argv tokens (quotes supported). */
export function splitCustomArgs(input: string): string[] {
  const trimmed = input.trim();
  if (!trimmed) {
    return [];
  }
  const tokens: string[] = [];
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(trimmed)) !== null) {
    tokens.push(match[1] ?? match[2] ?? match[3] ?? "");
  }
  return tokens.filter((t) => t.length > 0);
}

export const DEFAULT_CONFIG_FILE = "aspls.clingo.json";

export const SAMPLE_CLINGO_CONFIG = `{
  "models": 0,
  "threads": 1,
  "customArgs": "",
  "additionalFiles": []
}
`;

export function isValidModels(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

export function mergeClingoFileConfig(
  existing: Record<string, unknown>,
  patch: { models?: number; additionalFiles?: string[] },
): Record<string, unknown> {
  const next: Record<string, unknown> = { ...existing };
  if (patch.models !== undefined) {
    next.models = patch.models;
  }
  if (patch.additionalFiles !== undefined) {
    next.additionalFiles = patch.additionalFiles;
  }
  return next;
}

/** Prefer a workspace-relative path when `absPath` is under `workspaceRoot`. */
export function toWorkspaceRelativePath(
  absPath: string,
  workspaceRoot: string,
): string {
  const root = path.resolve(workspaceRoot);
  const full = path.resolve(absPath);
  const rel = path.relative(root, full);
  if (rel.startsWith("..") || path.isAbsolute(rel)) {
    return full;
  }
  return rel;
}

/**
 * Canonical pool rules (must stay in sync with server workspace_index.py resolve_pool):
 *
 * | additionalFiles (raw config) | Pool                                          |
 * |------------------------------|-----------------------------------------------|
 * | undefined / absent           | full-workspace fallback (discoveredUris)       |
 * | []  (explicit empty array)   | active file only                              |
 * | ["a.lp", ...]                | active file + resolved entries                |
 *
 * Resolution order per entry: activeDir first, then workspaceRoot.
 *
 * This function operates on already-resolved absolute paths (post resolveAdditionalFiles).
 */
export function resolvePool(opts: {
  primaryFile: string;
  additionalFiles: string[];
  /** True when additionalFiles came from an explicit config key (even if empty). */
  additionalFilesExplicit: boolean;
  discoveredFiles: string[];
}): string[] {
  if (!opts.additionalFilesExplicit) {
    return dedupePaths(opts.discoveredFiles);
  }
  return dedupePaths([opts.primaryFile, ...opts.additionalFiles]);
}

export function dedupePaths(paths: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const p of paths) {
    if (seen.has(p)) {
      continue;
    }
    seen.add(p);
    out.push(p);
  }
  return out;
}

export function removePathEntry(paths: string[], toRemove: string): string[] {
  return paths.filter((p) => p !== toRemove);
}
