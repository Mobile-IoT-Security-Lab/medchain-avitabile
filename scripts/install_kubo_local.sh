#!/usr/bin/env bash
set -euo pipefail

# Install Kubo (IPFS) locally into the repository under tools/kubo.
# No root required. Uses env KUBO_VERSION to pin version (default v0.27.0).
#
# Usage:
#   bash scripts/install_kubo_local.sh [install_dir]
#
# Result:
#   tools/kubo/ipfs (or $1/ipfs) becomes available

VERSION=${KUBO_VERSION:-v0.27.0}
INSTALL_DIR=${1:-tools/kubo}

OS=$(uname -s)
ARCH=$(uname -m)

case "$OS" in
  Linux) OS_NAME=linux ;;
  Darwin) OS_NAME=darwin ;;
  *) echo "Unsupported OS: $OS" >&2; exit 1 ;;
esac

case "$ARCH" in
  x86_64|amd64) ARCH_NAME=amd64 ;;
  aarch64|arm64) ARCH_NAME=arm64 ;;
  *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;;
esac

TARBALL="kubo_${VERSION}_${OS_NAME}-${ARCH_NAME}.tar.gz"
BASE_URL="https://dist.ipfs.tech/kubo/${VERSION}"
URL="${BASE_URL}/${TARBALL}"

echo "Installing Kubo ${VERSION} for ${OS_NAME}-${ARCH_NAME} into ${INSTALL_DIR}" 
mkdir -p "${INSTALL_DIR}"

TMPDIR=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "Downloading ${URL} ..."
curl -fsSL "${URL}" -o "$TMPDIR/${TARBALL}"

echo "Extracting ..."
tar -C "$TMPDIR" -xzf "$TMPDIR/${TARBALL}"

if [[ ! -x "$TMPDIR/kubo/ipfs" ]]; then
  echo "ipfs binary not found in archive" >&2
  exit 1
fi

echo "Placing binary ..."
mv "$TMPDIR/kubo/ipfs" "$INSTALL_DIR/ipfs"
chmod +x "$INSTALL_DIR/ipfs"

echo "Kubo installed at ${INSTALL_DIR}/ipfs"
"$INSTALL_DIR/ipfs" version

