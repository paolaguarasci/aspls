#!/usr/bin/env bash
set -euo pipefail

PUBLISHER="${OVSX_PUBLISHER:-pingflood}"
PKG="package.json"
BACKUP=".package.json.bak"

cp "$PKG" "$BACKUP"
node -e "
  const fs = require('fs');
  const p = JSON.parse(fs.readFileSync('$PKG', 'utf8'));
  p.publisher = process.env.OVSX_PUBLISHER || 'pingflood';
  fs.writeFileSync('$PKG', JSON.stringify(p, null, 4) + '\n');
"

npx vsce package -o "/tmp/aspls-openvsx.vsix"
npx ovsx publish "/tmp/aspls-openvsx.vsix" -p "${OVSX_PAT:?Set OVSX_PAT}"

mv "$BACKUP" "$PKG"