import { execFile } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { promisify } from "util";
import {
  normalizeClingoJson,
  parseClingoJsonStdout,
  type ClingoJsonResult,
} from "./clingoResultParse";
import type { ClingoRunOutcome, ClingoRunRequest } from "./clingoTypes";

const execFileAsync = promisify(execFile);

async function isWorkingClingo(executable: string): Promise<boolean> {
  try {
    const { stdout, stderr } = await execFileAsync(executable, ["--version"], {
      timeout: 5000,
    });
    const text = `${stdout}\n${stderr}`.toLowerCase();
    return text.includes("clingo");
  } catch {
    return false;
  }
}

export async function findClingoBinary(
  configuredPath: string | undefined,
): Promise<string | null> {
  if (configuredPath?.trim() && (await isWorkingClingo(configuredPath.trim()))) {
    return configuredPath.trim();
  }
  if (await isWorkingClingo("clingo")) {
    return "clingo";
  }
  return null;
}

function buildProgramWithIncludes(
  primaryFile: string,
  program: string,
  additionalFiles: string[],
): string {
  const parts: string[] = [`% === ${path.basename(primaryFile)} ===`, program];
  for (const file of additionalFiles) {
    let content: string;
    try {
      content = fs.readFileSync(file, "utf8");
    } catch (err) {
      throw new Error(`Cannot read additional file '${file}': ${String(err)}`);
    }
    parts.push(`% === ${path.basename(file)} ===`, content);
  }
  return parts.join("\n");
}

function buildArgv(
  files: string[],
  models: number,
  threads: number | undefined,
  customArgs: string[],
): string[] {
  const argv: string[] = [...files, String(models), "--outf=2"];
  if (threads !== undefined && threads > 0) {
    argv.push("-t", String(threads));
  }
  argv.push(...customArgs);
  return argv;
}

async function runPathClingo(
  request: ClingoRunRequest,
): Promise<ClingoRunOutcome> {
  const binary = await findClingoBinary(request.clingoPath);
  if (!binary) {
    return {
      ok: false,
      backend: "path",
      error:
        "Clingo binary not found on PATH. Install Clingo or disable 'aspls.clingo.usePath' to use the bundled WASM solver.",
      commandSummary: "clingo (not found)",
    };
  }

  for (const file of request.additionalFiles) {
    if (!fs.existsSync(file)) {
      return {
        ok: false,
        backend: "path",
        error: `Additional file not found: ${file}`,
        commandSummary: binary,
      };
    }
  }

  // Prefer the on-disk primary file so Clingo reports real paths in errors.
  // Write buffer contents to a temp sibling if the editor is unsaved? We pass
  // the editor text via stdin when it may differ — here we write a temp file
  // next to the primary only when needed. Simpler: always write a temp copy
  // of the buffer as the first input so unsaved edits are included.
  const tmpPrimary = path.join(
    os.tmpdir(),
    `aspls-${Date.now()}-${path.basename(request.primaryFile)}`,
  );
  fs.writeFileSync(tmpPrimary, request.program, "utf8");

  const files = [tmpPrimary, ...request.additionalFiles];
  const argv = buildArgv(
    files,
    request.models,
    request.threads,
    request.customArgs,
  );
  const commandSummary = `${binary} ${argv
    .map((a) => (a.includes(" ") ? `"${a}"` : a))
    .join(" ")}`;

  try {
    const { stdout, stderr } = await execFileAsync(binary, argv, {
      maxBuffer: 20 * 1024 * 1024,
      timeout: 120_000,
    });
    return parseClingoJsonStdout(stdout, stderr, "path", commandSummary, 10);
  } catch (err: unknown) {
    const execErr = err as {
      code?: number;
      stdout?: string;
      stderr?: string;
      message?: string;
    };
    // Clingo uses non-zero exit for UNSAT (20) and errors (65+) — still parse JSON.
    if (typeof execErr.stdout === "string" || typeof execErr.stderr === "string") {
      const outcome = parseClingoJsonStdout(
        execErr.stdout ?? "",
        execErr.stderr ?? "",
        "path",
        commandSummary,
        typeof execErr.code === "number" ? execErr.code : null,
      );
      try {
        fs.unlinkSync(tmpPrimary);
      } catch {
        /* ignore */
      }
      return outcome;
    }
    try {
      fs.unlinkSync(tmpPrimary);
    } catch {
      /* ignore */
    }
    return {
      ok: false,
      backend: "path",
      error: execErr.message ?? String(err),
      commandSummary,
    };
  } finally {
    try {
      if (fs.existsSync(tmpPrimary)) {
        fs.unlinkSync(tmpPrimary);
      }
    } catch {
      /* ignore */
    }
  }
}

async function runWasmClingo(
  request: ClingoRunRequest,
): Promise<ClingoRunOutcome> {
  const commandSummary = `clingo-wasm (models=${request.models})`;
  let program: string;
  try {
    program = buildProgramWithIncludes(
      request.primaryFile,
      request.program,
      request.additionalFiles,
    );
  } catch (err) {
    return {
      ok: false,
      backend: "wasm",
      error: String(err),
      commandSummary,
    };
  }

  // clingo-wasm options are fragile; only pass well-supported flags.
  const options: string[] = [];
  if (request.threads && request.threads > 1) {
    options.push("-t", String(request.threads));
  }
  // customArgs: pass through when present; WASM may reject some flags.
  options.push(...request.customArgs);

  try {
    // Dynamic require keeps activate light if WASM is never used.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const clingo = require("clingo-wasm") as {
      run: (
        program: string,
        models?: number,
        options?: string[],
      ) => Promise<ClingoJsonResult>;
    };
    const json = await clingo.run(
      program,
      request.models,
      options.length > 0 ? options : undefined,
    );
    const raw = JSON.stringify(json, null, 2);
    return normalizeClingoJson(json, "wasm", commandSummary, raw);
  } catch (err) {
    return {
      ok: false,
      backend: "wasm",
      error: String(err),
      commandSummary,
    };
  }
}

export async function runClingo(
  request: ClingoRunRequest,
): Promise<ClingoRunOutcome> {
  if (request.usePath) {
    return runPathClingo(request);
  }
  return runWasmClingo(request);
}
