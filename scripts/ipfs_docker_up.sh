#!/usr/bin/env bash
# Spin up an IPFS (Kubo) node in Docker, removing any existing container first.
# Ports are configurable via environment variables; defaults match common local usage.
#
# Usage:
#   bash scripts/ipfs_docker_up.sh
#
# Env vars (optional):
#   CONTAINER_NAME   - Docker container name (default: ipfs_host)
#   SWARM_PORT       - Host port for swarm (maps to 4001 in container) (default: 4001)
#   API_PORT         - Host port for API  (maps to 5001 in container) (default: 5001)
#   GATEWAY_PORT     - Host port for gateway (maps to 8080 in container) (default: 8081)
#   IPFS_IMAGE       - Docker image (default: ipfs/kubo:latest)

set -euo pipefail

CN=${CONTAINER_NAME:-ipfs_host}
SWARM_PORT=${SWARM_PORT:-4001}
API_PORT=${API_PORT:-5001}
GATEWAY_PORT=${GATEWAY_PORT:-8081}
IMAGE=${IPFS_IMAGE:-ipfs/kubo:latest}

echo "Removing existing container (if any): $CN"
docker rm -f "$CN" 2>/dev/null || true

echo "Starting IPFS (Kubo) container: $CN"
echo "  Swarm:   host ${SWARM_PORT} -> container 4001"
echo "  API:     host ${API_PORT} -> container 5001"
echo "  Gateway: host ${GATEWAY_PORT} -> container 8080"

docker run -d \
  --name "$CN" \
  -p ${SWARM_PORT}:4001 \
  -p ${API_PORT}:5001 \
  -p ${GATEWAY_PORT}:8080 \
  "$IMAGE" daemon

echo "Waiting for IPFS API to become ready ..."
for i in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/api/v0/version" >/dev/null; then
    echo "IPFS API is reachable"
    break
  fi
  sleep 0.5
done
curl -sS "http://127.0.0.1:${API_PORT}/api/v0/version" || true

if python3 -c "import ipfshttpclient" 2>/dev/null; then
  echo "Running pytest integration against IPFS API on port ${API_PORT}"
  USE_REAL_IPFS=1 IPFS_API_ADDR=/ip4/127.0.0.1/tcp/${API_PORT}/http IPFS_CONNECT_RETRIES=10 IPFS_CONNECT_BACKOFF_BASE=0.25 pytest -q tests/test_real_ipfs_integration.py || true
else
  echo "ipfshttpclient not available in Python environment; skipping pytest integration."
  echo "Install deps (pip install -r requirements.txt) and re-run: make ipfs-test IPFS_API_ADDR=/ip4/127.0.0.1/tcp/${API_PORT}/http"
fi
