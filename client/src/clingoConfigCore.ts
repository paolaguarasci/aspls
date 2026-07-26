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
