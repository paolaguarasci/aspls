import { execFile } from "child_process";
import { promisify } from "util";
import * as fs from "fs";
import * as path from "path";

const execFileAsync = promisify(execFile);

async function isWorkingPython(executable: string): Promise<boolean> {
  try {
    const { stdout } = await execFileAsync(executable, ["--version"]);
    return stdout.toLowerCase().includes("python 3") || stdout.toLowerCase().includes("python 3");
  } catch {
    return false;
  }
}

export async function findPythonInterpreter(
  configuredPath: string | undefined
): Promise<string | null> {
  if (configuredPath && (await isWorkingPython(configuredPath))) {
    return configuredPath;
  }
  for (const candidate of ["python3", "python"]) {
    if (await isWorkingPython(candidate)) {
      return candidate;
    }
  }
  return null;
}

function venvPythonPath(venvDir: string): string {
  return process.platform === "win32"
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");
}

export async function ensureServerVenv(
  globalStorageDir: string,
  pythonInterpreter: string,
  requirementsPath: string
): Promise<string> {
  const venvDir = path.join(globalStorageDir, "venv");
  const venvPython = venvPythonPath(venvDir);

  if (!fs.existsSync(venvPython)) {
    fs.mkdirSync(globalStorageDir, { recursive: true });
    try {
      await execFileAsync(pythonInterpreter, ["-m", "venv", venvDir]);
      await execFileAsync(venvPython, ["-m", "pip", "install", "-r", requirementsPath]);
    } catch (err) {
      throw new Error(
        `Failed to set up the ASP language server's Python environment: ${err}`
      );
    }
  }

  return venvPython;
}
