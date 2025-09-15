#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CIRCUITS_DIR="$(cd "$HERE/.." && pwd)"
BUILD_DIR="$CIRCUITS_DIR/build"

echo "[circuits] Removing $BUILD_DIR ..."
rm -rf "$BUILD_DIR"
echo "[circuits] Clean complete."

