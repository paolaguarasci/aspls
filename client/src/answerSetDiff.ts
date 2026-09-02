export interface AtomDiff {
  added: string[];
  removed: string[];
  unchanged: string[];
}

/** Set difference between two answer-set atom lists (order preserved in each bucket). */
export function diffAtomSets(
  prev: readonly string[],
  curr: readonly string[],
): AtomDiff {
  const prevSet = new Set(prev);
  const currSet = new Set(curr);
  const added: string[] = [];
  const removed: string[] = [];
  const unchanged: string[] = [];
  for (const atom of curr) {
    if (prevSet.has(atom)) {
      unchanged.push(atom);
    } else {
      added.push(atom);
    }
  }
  for (const atom of prev) {
    if (!currSet.has(atom)) {
      removed.push(atom);
    }
  }
  return { added, removed, unchanged };
}
