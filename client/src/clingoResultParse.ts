import type {
  ClingoAnswerSet,
  ClingoBackend,
  ClingoRunFailure,
  ClingoRunSuccess,
} from "./clingoTypes";

/** Subset of Clingo `--outf=2` / clingo-wasm JSON. */
export interface ClingoJsonResult {
  Solver?: string;
  Result?: string;
  Calls?: number;
  Call?: {
    Witnesses?: {
      Value?: string[];
      Costs?: number[];
    }[];
  }[];
  Models?: {
    More?: string;
    Number?: number;
  };
  Time?: {
    Total?: number;
  };
  Warnings?: string[];
  Error?: string;
}

export function isClingoErrorPayload(
  value: ClingoJsonResult,
): value is ClingoJsonResult & { Result: "ERROR"; Error: string } {
  return value.Result === "ERROR" && typeof value.Error === "string";
}

export function normalizeClingoJson(
  json: ClingoJsonResult,
  backend: ClingoBackend,
  commandSummary: string,
  raw: string,
): ClingoRunSuccess | ClingoRunFailure {
  if (isClingoErrorPayload(json)) {
    return {
      ok: false,
      backend,
      error: json.Error.trim() || "Clingo reported an error.",
      raw,
      commandSummary,
    };
  }

  const result = (json.Result ?? "UNKNOWN") as ClingoRunSuccess["result"];
  if (
    result !== "SATISFIABLE" &&
    result !== "UNSATISFIABLE" &&
    result !== "UNKNOWN" &&
    result !== "OPTIMUM FOUND"
  ) {
    return {
      ok: false,
      backend,
      error: `Unexpected Clingo result: ${String(json.Result)}`,
      raw,
      commandSummary,
    };
  }

  const answerSets: ClingoAnswerSet[] = [];
  const calls = json.Call ?? [];
  let index = 1;
  for (const call of calls) {
    for (const witness of call.Witnesses ?? []) {
      answerSets.push({
        index: index++,
        atoms: [...(witness.Value ?? [])],
        costs: witness.Costs ? [...witness.Costs] : undefined,
      });
    }
  }

  const warnings = (json.Warnings ?? [])
    .map((w) => w.trim())
    .filter((w) => w.length > 0);

  return {
    ok: true,
    backend,
    result,
    answerSets,
    more: json.Models?.More === "yes",
    modelCount: json.Models?.Number ?? answerSets.length,
    solver: json.Solver,
    timeTotal: json.Time?.Total,
    warnings,
    raw,
    commandSummary,
  };
}

/** Parse JSON stdout from `clingo --outf=2`. */
export function parseClingoJsonStdout(
  stdout: string,
  stderr: string,
  backend: ClingoBackend,
  commandSummary: string,
  exitCode: number | null,
): ClingoRunSuccess | ClingoRunFailure {
  const raw = [stdout, stderr].filter(Boolean).join("\n").trim();
  const trimmed = stdout.trim();

  if (!trimmed) {
    return {
      ok: false,
      backend,
      error:
        stderr.trim() ||
        `Clingo produced no output (exit code ${exitCode ?? "?"}).`,
      raw,
      commandSummary,
    };
  }

  let json: ClingoJsonResult;
  try {
    json = JSON.parse(trimmed) as ClingoJsonResult;
  } catch {
    // Fall back: surface text output (human-readable mode or corrupt JSON).
    if (exitCode !== null && exitCode !== 0 && exitCode !== 10 && exitCode !== 20 && exitCode !== 30) {
      return {
        ok: false,
        backend,
        error: stderr.trim() || trimmed || `Clingo failed (exit ${exitCode}).`,
        raw,
        commandSummary,
      };
    }
    return {
      ok: false,
      backend,
      error: `Could not parse Clingo JSON output.\n${stderr.trim() || trimmed}`,
      raw,
      commandSummary,
    };
  }

  const normalized = normalizeClingoJson(json, backend, commandSummary, raw);
  if (!normalized.ok && stderr.trim()) {
    return { ...normalized, error: stderr.trim() };
  }
  if (normalized.ok && stderr.trim()) {
    const extra = stderr
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean);
    return {
      ...normalized,
      warnings: [...normalized.warnings, ...extra],
    };
  }
  if (!normalized.ok && !normalized.error && stderr.trim()) {
    return { ...normalized, error: stderr.trim() };
  }
  return normalized;
}
