/** Normalized Clingo run outcome for the results UI. */
export type ClingoBackend = "path" | "wasm";

export interface ClingoAnswerSet {
  index: number;
  atoms: string[];
  costs?: number[];
}

export interface ClingoRunSuccess {
  ok: true;
  backend: ClingoBackend;
  result: "SATISFIABLE" | "UNSATISFIABLE" | "UNKNOWN" | "OPTIMUM FOUND";
  answerSets: ClingoAnswerSet[];
  more: boolean;
  modelCount: number;
  solver?: string;
  timeTotal?: number;
  warnings: string[];
  raw: string;
  commandSummary: string;
}

export interface ClingoRunFailure {
  ok: false;
  backend: ClingoBackend;
  error: string;
  raw?: string;
  commandSummary: string;
}

export type ClingoRunOutcome = ClingoRunSuccess | ClingoRunFailure;

export interface ClingoRunRequest {
  /** Absolute path of the primary .lp / .asp file. */
  primaryFile: string;
  /** Program text (saved or editor buffer). */
  program: string;
  /** Number of models: 1 = first, 0 = all. */
  models: number;
  /** Absolute paths of additional files. */
  additionalFiles: string[];
  threads?: number;
  customArgs: string[];
  usePath: boolean;
  /** Explicit binary path; empty = look up `clingo` on PATH. */
  clingoPath: string;
}

export interface ClingoResolvedConfig {
  models: number;
  threads: number;
  customArgs: string;
  additionalFiles: string[];
  usePath: boolean;
  clingoPath: string;
  configFileName: string;
}
