#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/common.sh"

ZKEY="$BUILD_DIR/redaction_final.zkey"
if [ ! -f "$ZKEY" ]; then
  echo "Error: missing $ZKEY (run setup.sh)" >&2
  exit 1
fi

OUT_SOL="$CONTRACTS_DIR/src/RedactionVerifier_groth16.sol"

echo "[circuits] Exporting Solidity verifier to $OUT_SOL ..."
"$SNARKJS" zkey export solidityverifier "$ZKEY" "$OUT_SOL"

echo "// Wrapper alias to keep previous naming convention" >> "$OUT_SOL"
echo "contract RedactionVerifier is Verifier {}" >> "$OUT_SOL"

echo "[circuits] Verifier contract exported. You can now compile contracts."

