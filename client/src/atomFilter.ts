/** Returns true when `atom` matches a non-empty filter query (case-insensitive substring). */
export function atomMatchesFilter(atom: string, query: string): boolean {
  const q = query.trim();
  if (!q) {
    return true;
  }
  return atom.toLowerCase().includes(q.toLowerCase());
}

/** Keeps atoms that match `query`; empty query returns all atoms. */
export function filterAtoms(atoms: string[], query: string): string[] {
  const q = query.trim();
  if (!q) {
    return atoms;
  }
  return atoms.filter((a) => atomMatchesFilter(a, query));
}
