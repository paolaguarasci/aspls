#!/usr/bin/env bash
set -euo pipefail

# Always run against the extension manifest in client/ (not the workspace root).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PUBLISHER="${OVSX_PUBLISHER:-pingflood}"
PKG="package.json"
BACKUP=".package.json.bak"

cp "$PKG" "$BACKUP"
restore() { mv -f "$BACKUP" "$PKG"; }
trap restore EXIT

node -e "
  const fs = require('fs');
  const p = JSON.parse(fs.readFileSync('$PKG', 'utf8'));
  p.publisher = process.env.OVSX_PUBLISHER || 'pingflood';
  fs.writeFileSync('$PKG', JSON.stringify(p, null, 4) + '\n');
"

npx --yes @vscode/vsce package -o "/tmp/aspls-openvsx.vsix"

if [[ -n "${OVSX_PAT:-}" ]]; then
  npx --yes ovsx publish "/tmp/aspls-openvsx.vsix" -p "$OVSX_PAT"
else
  echo "OVSX_PAT not set. Prefer GitHub Actions → Publish Open VSX (OIDC)," >&2
  echo "or: OVSX_PAT=… npm run publish:openvsx" >&2
  exit 1
fi
