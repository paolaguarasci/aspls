/**
 * ASPLS-33 — extension packaging smoke for VS Code and Cursor (Open VSX).
 * Both editors consume the same VSIX; vsce package validates manifest + bundle.
 */
import * as assert from "assert";
import * as child_process from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const CLIENT_ROOT = path.join(__dirname, "..");

function run(cmd: string, args: string[], cwd: string): string {
  const result = child_process.spawnSync(cmd, args, {
    cwd,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (result.status !== 0) {
    throw new Error(
      `${cmd} ${args.join(" ")} failed (${result.status}): ${result.stderr || result.stdout}`,
    );
  }
  return result.stdout;
}

function main(): void {
  const pkg = JSON.parse(
    fs.readFileSync(path.join(CLIENT_ROOT, "package.json"), "utf8"),
  ) as {
    engines?: { vscode?: string };
    main?: string;
    publisher?: string;
    name?: string;
    version?: string;
  };

  assert.ok(
    pkg.engines?.vscode,
    "engines.vscode required for VS Code and Cursor",
  );
  assert.ok(pkg.main, "main entry required");
  assert.ok(
    pkg.publisher && pkg.name && pkg.version,
    "publisher, name, and version required",
  );

  const listed = run("npx", ["vsce", "ls"], CLIENT_ROOT);
  assert.ok(
    listed.includes("out/extension.js"),
    "vsce ls must include extension entry",
  );
  assert.ok(
    listed.includes("server/server.py"),
    "vsce ls must include bundled LSP server",
  );

  const vsixPath = path.join(os.tmpdir(), `aspls-smoke-${Date.now()}.vsix`);
  try {
    run(
      "npx",
      ["vsce", "package", "--no-dependencies", "-o", vsixPath],
      CLIENT_ROOT,
    );
    assert.ok(fs.existsSync(vsixPath), "vsce package must produce a VSIX");
    assert.ok(
      fs.statSync(vsixPath).size > 10_000,
      "VSIX must be non-trivial size",
    );
  } finally {
    if (fs.existsSync(vsixPath)) {
      fs.unlinkSync(vsixPath);
    }
  }

  console.log(
    "extensionPackage.smoke.test.ts: ok (VS Code + Cursor / Open VSX package)",
  );
}

void main();
