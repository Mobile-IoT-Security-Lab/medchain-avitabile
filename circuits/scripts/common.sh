#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CIRCUITS_DIR="$(cd "$HERE/.." && pwd)"
BUILD_DIR="$CIRCUITS_DIR/build"
PROJECT_ROOT="$(cd "$CIRCUITS_DIR/.." && pwd)"
CONTRACTS_DIR="$PROJECT_ROOT/contracts"

# Find circom binary
if command -v circom >/dev/null 2>&1; then
  CIRCOM="$(command -v circom)"
else
  echo "Error: circom not found in PATH. Please install Circom v2.x" >&2
  exit 1
fi

# Prefer snarkjs from contracts/node_modules, fallback to PATH
if [ -x "$CONTRACTS_DIR/node_modules/.bin/snarkjs" ]; then
  SNARKJS="$CONTRACTS_DIR/node_modules/.bin/snarkjs"
elif command -v snarkjs >/dev/null 2>&1; then
  SNARKJS="$(command -v snarkjs)"
else
  echo "Error: snarkjs not found. Run 'cd contracts && npm i' or install globally." >&2
  exit 1
fi

mkdir -p "$BUILD_DIR"

