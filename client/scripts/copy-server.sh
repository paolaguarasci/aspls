#!/usr/bin/env bash
set -euo pipefail
rm -rf "$(dirname "$0")/../server"
cp -r "$(dirname "$0")/../../server" "$(dirname "$0")/../server"
