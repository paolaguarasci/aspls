import * as fs from "fs";
import * as path from "path";

const INCLUDE_RE = /#include\s+"([^"]+)"\s*\./g;

/** Extract #include paths from ASP source (without quotes). */
export function extractIncludes(text: string): string[] {
  const paths: string[] = [];
  const re = new RegExp(INCLUDE_RE.source, "g");
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    paths.push(match[1]);
  }
  return paths;
}

function resolveIncludePath(
  includingFile: string,
  includePath: string,
  workspaceRoot: string | undefined,
): string {
  if (path.isAbsolute(includePath)) {
    return includePath;
  }
  const fromPrimary = path.resolve(path.dirname(includingFile), includePath);
  if (fs.existsSync(fromPrimary)) {
    return fromPrimary;
  }
  if (workspaceRoot) {
    const fromRoot = path.resolve(workspaceRoot, includePath);
    if (fs.existsSync(fromRoot)) {
      return fromRoot;
    }
  }
  return fromPrimary;
}

/**
 * Inline #include directives for WASM (and other single-string backends).
 * Preserves include order; skips cycles.
 */
export function expandIncludesInProgram(
  primaryFile: string,
  program: string,
  workspaceRoot: string | undefined,
  seen: Set<string> = new Set(),
): string {
  const parts: string[] = [];
  let lastIndex = 0;
  const re = new RegExp(INCLUDE_RE.source, "g");
  let match: RegExpExecArray | null;

  while ((match = re.exec(program)) !== null) {
    parts.push(program.slice(lastIndex, match.index));
    const incPath = resolveIncludePath(primaryFile, match[1], workspaceRoot);
    if (!seen.has(incPath)) {
      seen.add(incPath);
      let content: string;
      try {
        content = fs.readFileSync(incPath, "utf8");
      } catch (err) {
        throw new Error(`Cannot read included file '${incPath}': ${String(err)}`);
      }
      parts.push(
        expandIncludesInProgram(incPath, content, workspaceRoot, seen),
      );
    }
    lastIndex = re.lastIndex;
  }
  parts.push(program.slice(lastIndex));
  return parts.join("");
}

/** Collect absolute paths of all transitively included files. */
export function collectIncludedFiles(
  primaryFile: string,
  program: string,
  workspaceRoot: string | undefined,
): string[] {
  const seen = new Set<string>();
  const queue = [...extractIncludes(program)];
  const out: string[] = [];
  while (queue.length > 0) {
    const rel = queue.shift()!;
    const abs = resolveIncludePath(primaryFile, rel, workspaceRoot);
    if (seen.has(abs)) {
      continue;
    }
    seen.add(abs);
    out.push(abs);
    let content: string;
    try {
      content = fs.readFileSync(abs, "utf8");
    } catch {
      continue;
    }
    queue.push(...extractIncludes(content));
  }
  return out;
}
