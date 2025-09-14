#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/common.sh"

echo "[circuits] Compiling redaction.circom ..."
"$CIRCOM" "$CIRCUITS_DIR/redaction.circom" \
  --r1cs --wasm --sym \
  -o "$BUILD_DIR"

echo "[circuits] Done. Outputs in: $BUILD_DIR"

