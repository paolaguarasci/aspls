/**
 * WASM vs PATH capability matrix and detection of fragile Clingo CLI args.
 * Keep in sync with the README "Capability matrix" section.
 */

export type CapabilitySupport = "yes" | "limited" | "no";

export interface CapabilityRow {
  feature: string;
  wasm: CapabilitySupport;
  path: CapabilitySupport;
  notes?: string;
}

/** Documented matrix (also rendered in client/README.md). */
export const CLINGO_CAPABILITY_MATRIX: readonly CapabilityRow[] = [
  {
    feature: "Basic programs / answer sets",
    wasm: "yes",
    path: "yes",
  },
  {
    feature: "Multi-file via additionalFiles",
    wasm: "limited",
    path: "yes",
    notes:
      "clingo-wasm accepts one program string; WASM concatenates additionalFiles and inlines #include; PATH passes real files",
  },
  {
    feature: "models / -n (via aspls UI)",
    wasm: "yes",
    path: "yes",
  },
  {
    feature: "--const / -c",
    wasm: "yes",
    path: "yes",
  },
  {
    feature: "Threads (-t)",
    wasm: "limited",
    path: "yes",
    notes: "WASM accepts -t but gains are modest in the extension host",
  },
  {
    feature: "Output control (--outf, -q, --stats, --verbose)",
    wasm: "no",
    path: "yes",
    notes: "aspls already consumes structured JSON; do not set --outf in customArgs",
  },
  {
    feature: "Advanced CLI (--parallel-mode, --configuration, Lua, limits)",
    wasm: "no",
    path: "yes",
    notes: "Enable aspls.clingo.usePath for native Clingo",
  },
] as const;

/**
 * Patterns for customArgs that are unreliable or meaningless under clingo-wasm.
 * Matching is case-sensitive on the flag token (Clingo CLI style).
 */
const FRAGILE_WASM_FLAG_PATTERNS: readonly RegExp[] = [
  /^--outf(=|$)/,
  /^-n(=|$)/,
  /^--quiet$/,
  /^-q$/,
  /^--verbose$/,
  /^-V$/,
  /^--stats(=|$)/,
  /^--out-/,
  /^--parallel-mode(=|$)/,
  /^--configuration(=|$)/,
  /^--lua/,
  /^--pre$/,
  /^--profile(=|$)/,
  /^--time-limit(=|$)/,
  /^--solve-limit(=|$)/,
  /^--opt-strategy(=|$)/,
  /^--opt-heuristic(=|$)/,
];

/** Tokens that are values for a previous fragile flag (e.g. `--outf` `2`). */
const FRAGILE_VALUE_FOLLOWING = new Set([
  "--outf",
  "-n",
  "--stats",
  "--parallel-mode",
  "--configuration",
  "--time-limit",
  "--solve-limit",
  "--opt-strategy",
  "--opt-heuristic",
]);

export function isFragileWasmFlag(token: string): boolean {
  return FRAGILE_WASM_FLAG_PATTERNS.some((re) => re.test(token));
}

/**
 * Return customArgs tokens that are fragile under WASM (flags and their
 * immediate bare values when the flag is not `--flag=value`).
 */
export function findFragileWasmArgs(customArgs: string[]): string[] {
  const fragile: string[] = [];
  for (let i = 0; i < customArgs.length; i++) {
    const token = customArgs[i];
    if (isFragileWasmFlag(token)) {
      fragile.push(token);
      const base = token.split("=")[0];
      if (
        !token.includes("=") &&
        FRAGILE_VALUE_FOLLOWING.has(base) &&
        i + 1 < customArgs.length &&
        !customArgs[i + 1].startsWith("-")
      ) {
        fragile.push(customArgs[i + 1]);
        i += 1;
      }
      continue;
    }
  }
  return fragile;
}

export function formatWasmFragileArgsWarning(fragileArgs: string[]): string {
  const listed = fragileArgs.map((a) => `  - ${a}`).join("\n");
  return formatWasmToPathSuggestion(listed);
}

export function formatWasmToPathSuggestion(listedItems: string): string {
  return (
    "WASM capability warning: these settings need native Clingo (enable aspls.clingo.usePath):\n" +
    `${listedItems}\n` +
    "Fix: enable aspls.clingo.usePath (and install Clingo) for full CLI support, " +
    "or adjust aspls.clingo.threads / aspls.clingo.customArgs / aspls.clingo.json."
  );
}

/**
 * Non-blocking WASM → PATH suggestions for the active backend. Empty when PATH
 * or when customArgs and threads look safe for WASM.
 */
export function collectBackendCapabilityWarnings(opts: {
  usePath: boolean;
  customArgs: string[];
  threads?: number;
}): string[] {
  if (opts.usePath) {
    return [];
  }
  const lines: string[] = [];
  const fragile = findFragileWasmArgs(opts.customArgs);
  for (const arg of fragile) {
    lines.push(`  - ${arg} (unreliable customArg)`);
  }
  if (opts.threads !== undefined && opts.threads > 1) {
    lines.push(`  - threads=${opts.threads} (limited under WASM)`);
  }
  if (lines.length === 0) {
    return [];
  }
  return [formatWasmToPathSuggestion(lines.join("\n"))];
}
