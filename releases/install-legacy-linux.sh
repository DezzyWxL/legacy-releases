#!/usr/bin/env bash
set -euo pipefail

CORE_PACKAGE="${1:-legacy-core-1.0.0.tgz}"
CLI_PACKAGE="${2:-legacy-cli-1.0.0.tgz}"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js (>=18) is required." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required." >&2
  exit 1
fi

if [ ! -f "$CORE_PACKAGE" ]; then
  echo "Missing $CORE_PACKAGE in current folder." >&2
  exit 1
fi

if [ ! -f "$CLI_PACKAGE" ]; then
  echo "Missing $CLI_PACKAGE in current folder." >&2
  exit 1
fi

npm install -g "./$CORE_PACKAGE" "./$CLI_PACKAGE"
echo "Installed. Run: legacy"
