import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";
import {
  DEFAULT_CONFIG_FILE,
  SAMPLE_CLINGO_CONFIG,
  splitCustomArgs,
} from "./clingoConfigCore";
import type { ClingoResolvedConfig } from "./clingoTypes";

export { DEFAULT_CONFIG_FILE, SAMPLE_CLINGO_CONFIG, splitCustomArgs };

interface FileConfig {
  models?: number;
  threads?: number;
  customArgs?: string;
  additionalFiles?: string[];
}

function readWorkspaceConfigFile(
  configFileName: string,
): FileConfig | undefined {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    return undefined;
  }
  const name = configFileName.trim() || DEFAULT_CONFIG_FILE;
  for (const folder of folders) {
    const full = path.join(folder.uri.fsPath, name);
    if (!fs.existsSync(full)) {
      continue;
    }
    try {
      const raw = fs.readFileSync(full, "utf8");
      const parsed = JSON.parse(raw) as FileConfig;
      return parsed;
    } catch (err) {
      throw new Error(
        `Failed to read Clingo config file '${full}': ${String(err)}`,
      );
    }
  }
  return undefined;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((v): v is string => typeof v === "string");
}

/**
 * Merge VS Code settings with an optional workspace config file.
 * File values override settings when present.
 */
export function resolveClingoConfig(options?: {
  /** When true, require the workspace config file (for "run with config"). */
  requireConfigFile?: boolean;
}): ClingoResolvedConfig {
  const cfg = vscode.workspace.getConfiguration("aspls");
  const configFileName =
    cfg.get<string>("clingo.configFile", DEFAULT_CONFIG_FILE) ||
    DEFAULT_CONFIG_FILE;

  const file = readWorkspaceConfigFile(configFileName);
  if (options?.requireConfigFile && !file) {
    throw new Error(
      `Clingo config file '${configFileName}' not found in the workspace. Run "aspls: Initialize Clingo config file" first.`,
    );
  }

  const settingsAdditional = asStringArray(
    cfg.get("clingo.additionalFiles", []),
  );

  return {
    models: file?.models ?? cfg.get<number>("clingo.models", 1),
    threads: file?.threads ?? cfg.get<number>("clingo.threads", 1),
    customArgs:
      file?.customArgs ?? cfg.get<string>("clingo.customArgs", "") ?? "",
    additionalFiles:
      file?.additionalFiles !== undefined
        ? asStringArray(file.additionalFiles)
        : settingsAdditional,
    usePath: cfg.get<boolean>("clingo.usePath", false),
    clingoPath: cfg.get<string>("clingo.path", "") ?? "",
    configFileName,
  };
}

/** Resolve additional file paths relative to the primary file's directory. */
export function resolveAdditionalFiles(
  primaryFile: string,
  relativeOrAbsolute: string[],
): string[] {
  const baseDir = path.dirname(primaryFile);
  const folders = vscode.workspace.workspaceFolders;
  const workspaceRoot = folders?.[0]?.uri.fsPath;

  return relativeOrAbsolute.map((entry) => {
    if (path.isAbsolute(entry)) {
      return entry;
    }
    const fromPrimary = path.resolve(baseDir, entry);
    if (fs.existsSync(fromPrimary)) {
      return fromPrimary;
    }
    if (workspaceRoot) {
      const fromRoot = path.resolve(workspaceRoot, entry);
      if (fs.existsSync(fromRoot)) {
        return fromRoot;
      }
    }
    return fromPrimary;
  });
}

export async function writeSampleConfigFile(
  configFileName: string,
): Promise<vscode.Uri> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    throw new Error("Open a workspace folder to create a Clingo config file.");
  }
  const name = configFileName.trim() || DEFAULT_CONFIG_FILE;
  const uri = vscode.Uri.joinPath(folders[0].uri, name);
  try {
    await vscode.workspace.fs.stat(uri);
    throw new Error(`Config file already exists: ${uri.fsPath}`);
  } catch (err) {
    if (
      err instanceof Error &&
      err.message.startsWith("Config file already exists")
    ) {
      throw err;
    }
  }
  await vscode.workspace.fs.writeFile(
    uri,
    Buffer.from(SAMPLE_CLINGO_CONFIG, "utf8"),
  );
  return uri;
}
