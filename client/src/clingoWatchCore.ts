import * as path from "path";
import { dedupePaths } from "./clingoConfigCore";

/** Whether a save event should trigger a debounced Clingo re-run. */
export function shouldWatchRerun(
  watchEnabled: boolean,
  lastFile: string | undefined,
  savedPath: string,
  poolPaths: string[],
): boolean {
  if (!watchEnabled || !lastFile) {
    return false;
  }
  const normalizedSaved = path.normalize(savedPath);
  return poolPaths.some((p) => path.normalize(p) === normalizedSaved);
}

export function buildWatchPool(
  primaryFile: string,
  additionalFiles: string[],
): string[] {
  return dedupePaths([primaryFile, ...additionalFiles]);
}

export function normalizeWatchDebounceMs(value: unknown, fallback = 500): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    return fallback;
  }
  return Math.floor(value);
}
