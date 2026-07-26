/** Reserved words that look like identifiers but are not predicates. */
const RESERVED = new Set(["not"]);

export type PredicateOccurrence = {
  name: string;
  line: number;
  start: number;
  end: number;
};

function isIdentStart(ch: string): boolean {
  return ch >= "a" && ch <= "z";
}

function isIdentChar(ch: string): boolean {
  return (
    (ch >= "a" && ch <= "z") ||
    (ch >= "A" && ch <= "Z") ||
    (ch >= "0" && ch <= "9") ||
    ch === "_"
  );
}

function nextNonWs(code: string, from: number): string {
  for (let i = from; i < code.length; i++) {
    const ch = code[i];
    if (ch !== " " && ch !== "\t") {
      return ch;
    }
  }
  return "";
}

function isAfterRangeDots(code: string, start: number): boolean {
  let i = start - 1;
  while (i >= 0 && (code[i] === " " || code[i] === "\t")) {
    i--;
  }
  return i >= 1 && code[i] === "." && code[i - 1] === ".";
}

function isAfterCompareOp(code: string, start: number): boolean {
  let i = start - 1;
  while (i >= 0 && (code[i] === " " || code[i] === "\t")) {
    i--;
  }
  if (i < 0) {
    return false;
  }
  if (i >= 1) {
    const two = code[i - 1] + code[i];
    if (two === "<=" || two === ">=" || two === "!=") {
      return true;
    }
  }
  return code[i] === "<" || code[i] === ">" || code[i] === "=";
}

/**
 * Find predicate-name occurrences in ASP source.
 * Skips line comments, `not`, `#`-directives, and constant terms inside (...).
 */
export function findPredicateOccurrences(text: string): PredicateOccurrence[] {
  const results: PredicateOccurrence[] = [];
  const lines = text.split("\n");

  for (let line = 0; line < lines.length; line++) {
    const raw = lines[line];
    const commentIdx = raw.indexOf("%");
    const code = commentIdx >= 0 ? raw.slice(0, commentIdx) : raw;

    let parenDepth = 0;
    let i = 0;
    while (i < code.length) {
      const ch = code[i];

      if (ch === "(") {
        parenDepth++;
        i++;
        continue;
      }
      if (ch === ")") {
        parenDepth = Math.max(0, parenDepth - 1);
        i++;
        continue;
      }

      if (isIdentStart(ch)) {
        const start = i;
        i++;
        while (i < code.length && isIdentChar(code[i])) {
          i++;
        }
        const name = code.slice(start, i);
        const prev = start > 0 ? code[start - 1] : "";

        if (
          RESERVED.has(name) ||
          prev === "#" ||
          isAfterRangeDots(code, start) ||
          isAfterCompareOp(code, start)
        ) {
          continue;
        }

        const next = nextNonWs(code, i);
        // pred(Args) or #show pred/N
        const isCallOrShow = next === "(" || next === "/";
        // nullary atom at top level (not a term inside parentheses)
        const isNullary =
          parenDepth === 0 &&
          next !== "=" &&
          next !== "(" &&
          next !== "/";

        if (isCallOrShow || isNullary) {
          // Inside parentheses, only calls count (terms like label(hello) skip hello).
          if (parenDepth > 0 && !isCallOrShow) {
            continue;
          }
          results.push({ name, line, start, end: i });
        }
        continue;
      }

      i++;
    }
  }

  return results;
}

/** Stable non-negative hash for a predicate name. */
export function hashPredicateName(name: string): number {
  let h = 2166136261;
  for (let i = 0; i < name.length; i++) {
    h ^= name.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function colorIndexForPredicate(
  name: string,
  paletteSize: number,
): number {
  if (paletteSize <= 0) {
    return 0;
  }
  return hashPredicateName(name) % paletteSize;
}

/** Group occurrence ranges by palette index. */
export function groupOccurrencesByColor(
  occurrences: PredicateOccurrence[],
  paletteSize: number,
): Map<number, PredicateOccurrence[]> {
  const groups = new Map<number, PredicateOccurrence[]>();
  for (const occ of occurrences) {
    const index = colorIndexForPredicate(occ.name, paletteSize);
    const list = groups.get(index);
    if (list) {
      list.push(occ);
    } else {
      groups.set(index, [occ]);
    }
  }
  return groups;
}
