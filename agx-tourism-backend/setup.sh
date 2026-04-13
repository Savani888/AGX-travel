#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="${1:-agx-tourism-backend}"

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

mkdir -p src/services src/utils src/middleware logs tests docs data/seed storage/documents

if [[ -f .env.example && ! -f .env ]]; then
  cp .env.example .env
fi

if command -v npm >/dev/null 2>&1; then
  npm install
else
  echo "npm is required but was not found on PATH."
  exit 1
fi

echo "Setup complete. Open the folder in VS Code and run: npm start"
