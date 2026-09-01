import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";
import {
  DEFAULT_CONFIG_FILE,
  asConstantsArray,
  asStringArray,
  formatClingoConfigFile,
  isValidModels,
  mergeClingoFileConfig,
  resolveConfigAdditionalFiles,
  SAMPLE_CLINGO_CONFIG,
  splitCustomArgs,
  type ClingoConstant,
  type ClingoFileSeed,
} from "./clingoConfigCore";
import type { ClingoResolvedConfig } from "./clingoTypes";

export { DEFAULT_CONFIG_FILE, SAMPLE_CLINGO_CONFIG, splitCustomArgs };

interface FileConfig {
  models?: number;
  threads?: number;
  customArgs?: string;
  constants?: unknown;
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

/** Exposed for deprecation warning: whether any workspace config defines additionalFiles. */
export function readClingoFileConfigState(): {
  configFileName: string;
  additionalFilesDefined: boolean;
} {
  const cfg = vscode.workspace.getConfiguration("aspls");
  const configFileName =
    cfg.get<string>("clingo.configFile", DEFAULT_CONFIG_FILE) ||
    DEFAULT_CONFIG_FILE;
  const file = readWorkspaceConfigFile(configFileName);
  return {
    configFileName,
    additionalFilesDefined: file?.additionalFiles !== undefined,
  };
}

function clingoSettingsSeed(): ClingoFileSeed {
  const cfg = vscode.workspace.getConfiguration("aspls");
  return {
    models: cfg.get<number>("clingo.models", 1),
    threads: cfg.get<number>("clingo.threads", 1),
    customArgs: cfg.get<string>("clingo.customArgs", "") ?? "",
    constants: [],
    additionalFiles: asStringArray(cfg.get("clingo.additionalFiles", [])),
  };
}

/**
 * Merge VS Code settings with an optional workspace config file.
 * File values override settings when present (except additionalFiles, which is config-file-only).
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

  const { additionalFiles, additionalFilesExplicit } =
    resolveConfigAdditionalFiles(file?.additionalFiles);

  return {
    models: file?.models ?? cfg.get<number>("clingo.models", 1),
    threads: file?.threads ?? cfg.get<number>("clingo.threads", 1),
    customArgs:
      file?.customArgs ?? cfg.get<string>("clingo.customArgs", "") ?? "",
    constants: asConstantsArray(file?.constants),
    additionalFiles,
    additionalFilesExplicit,
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
    Buffer.from(formatClingoConfigFile(clingoSettingsSeed()), "utf8"),
  );
  return uri;
}

/** Create the workspace Clingo config file if missing; return its URI. */
export async function ensureClingoConfigFile(
  configFileName?: string,
): Promise<vscode.Uri> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    throw new Error("Open a workspace folder to edit the Clingo config file.");
  }
  const name =
    (configFileName ?? resolveClingoConfig().configFileName).trim() ||
    DEFAULT_CONFIG_FILE;
  // Multi-root: write to folders[0], same as writeSampleConfigFile (Init Config).
  const uri = vscode.Uri.joinPath(folders[0].uri, name);
  try {
    await vscode.workspace.fs.stat(uri);
    return uri;
  } catch {
    // Seed from current settings so existing additionalFiles / threads / customArgs
    // are preserved when the Solver sidebar creates the config file.
    const body = formatClingoConfigFile(clingoSettingsSeed());
    await vscode.workspace.fs.writeFile(uri, Buffer.from(body, "utf8"));
    return uri;
  }
}

export async function patchClingoConfigFile(patch: {
  models?: number;
  additionalFiles?: string[];
  constants?: ClingoConstant[];
}): Promise<void> {
  if (patch.models !== undefined && !isValidModels(patch.models)) {
    throw new Error(`Invalid models value: ${String(patch.models)}`);
  }
  const uri = await ensureClingoConfigFile();
  let existing: Record<string, unknown> = {};
  try {
    const raw = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString(
      "utf8",
    );
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      existing = parsed as Record<string, unknown>;
    } else {
      throw new Error(`Clingo config is not a JSON object: ${uri.fsPath}`);
    }
  } catch (err) {
    if (
      err instanceof Error &&
      err.message.startsWith("Clingo config is not a JSON object")
    ) {
      throw err;
    }
    if (err instanceof SyntaxError) {
      throw new Error(
        `Failed to parse Clingo config file '${uri.fsPath}': ${err.message}`,
      );
    }
    throw err;
  }
  const merged = mergeClingoFileConfig(existing, patch);
  const body = `${JSON.stringify(merged, null, 2)}\n`;
  await vscode.workspace.fs.writeFile(uri, Buffer.from(body, "utf8"));
}

export async function updateClingoUsePath(usePath: boolean): Promise<void> {
  await vscode.workspace
    .getConfiguration("aspls")
    .update("clingo.usePath", usePath, vscode.ConfigurationTarget.Workspace);
}

export async function updateClingoPath(clingoPath: string): Promise<void> {
  await vscode.workspace
    .getConfiguration("aspls")
    .update("clingo.path", clingoPath, vscode.ConfigurationTarget.Workspace);
}
