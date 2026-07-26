#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$(cd "$(dirname "$0")/.." && pwd)/server"
rm -rf "$DEST"
mkdir -p "$DEST"
# Copy server sources only — skip local venvs, caches, and egg-info.
rsync -a \
  --exclude '.venv/' \
  --exclude '**/__pycache__/' \
  --exclude '*.egg-info/' \
  --exclude '.pytest_cache/' \
  "$ROOT/server/" "$DEST/"
