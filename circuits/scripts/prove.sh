#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/common.sh"

INPUT_JSON="${1:-$CIRCUITS_DIR/input/example.json}"
if [ ! -f "$INPUT_JSON" ]; then
  echo "Error: input JSON not found: $INPUT_JSON" >&2
  exit 1
fi

WASM="$BUILD_DIR/redaction_js/redaction.wasm"
ZKEY="$BUILD_DIR/redaction_final.zkey"
VK="$BUILD_DIR/verification_key.json"

for f in "$WASM" "$ZKEY" "$VK"; do
  if [ ! -f "$f" ]; then
    echo "Error: missing artifact: $f (run compile.sh and setup.sh)" >&2
    exit 1
  fi
done

echo "[circuits] Generating witness ..."
"$SNARKJS" wtns calculate "$WASM" "$INPUT_JSON" "$BUILD_DIR/witness.wtns"

echo "[circuits] Proving with Groth16 ..."
"$SNARKJS" groth16 prove "$ZKEY" "$BUILD_DIR/witness.wtns" "$BUILD_DIR/proof.json" "$BUILD_DIR/public.json"

echo "[circuits] Verifying ..."
"$SNARKJS" groth16 verify "$VK" "$BUILD_DIR/public.json" "$BUILD_DIR/proof.json"

echo "[circuits] Proof generated and verified. See $BUILD_DIR/proof.json and $BUILD_DIR/public.json"

