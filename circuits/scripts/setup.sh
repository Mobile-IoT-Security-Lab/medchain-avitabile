#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/common.sh"

R1CS="$BUILD_DIR/redaction.r1cs"
if [ ! -f "$R1CS" ]; then
  echo "[circuits] Missing $R1CS. Run compile.sh first." >&2
  exit 1
fi

# PTAU path may be provided by env PTAU or defaults to a common location under tools/
PTAU_DEFAULT="$PROJECT_ROOT/tools/powersOfTau28_hez_final_12.ptau"
PTAU_FILE="${PTAU:-$PTAU_DEFAULT}"

if [ ! -f "$PTAU_FILE" ]; then
  echo "Error: PTAU file not found at $PTAU_FILE" >&2
  echo "Provide the path via PTAU=... or place it at $PTAU_DEFAULT" >&2
  echo "Example download: curl -L -o $PTAU_DEFAULT https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_12.ptau" >&2
  exit 1
fi

echo "[circuits] Groth16 setup with $PTAU_FILE ..."
"$SNARKJS" groth16 setup "$R1CS" "$PTAU_FILE" "$BUILD_DIR/redaction_0000.zkey"

echo "[circuits] Finalizing zkey via beacon (non-interactive)..."
BEACON_HEX="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
"$SNARKJS" zkey beacon "$BUILD_DIR/redaction_0000.zkey" "$BUILD_DIR/redaction_final.zkey" "$BEACON_HEX" 10

echo "[circuits] Exporting verification key ..."
"$SNARKJS" zkey export verificationkey "$BUILD_DIR/redaction_final.zkey" "$BUILD_DIR/verification_key.json"

echo "[circuits] Setup complete. Artifacts in: $BUILD_DIR"
