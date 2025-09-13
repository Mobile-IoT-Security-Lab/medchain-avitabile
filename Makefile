.PHONY: help ipfs-test ipfs-check

IPFS_API_ADDR ?= /ip4/127.0.0.1/tcp/5001/http

help:
	@echo "Available targets:"
	@echo "  ipfs-test    Run real IPFS integration test (requires local daemon)"
	@echo "  ipfs-check   Query IPFS API version to verify connectivity"

ipfs-check:
	@echo "Checking IPFS API at $(IPFS_API_ADDR) ..."
	@python3 - << 'PY2'
import os, sys, json
addr = os.environ.get('IPFS_API_ADDR', '/ip4/127.0.0.1/tcp/5001/http')
try:
    import ipfshttpclient
    c = ipfshttpclient.connect(addr)
    print(json.dumps(c.version(), indent=2))
except Exception as e:
    print(f"Failed to reach IPFS API at {addr}: {e}")
    sys.exit(1)
PY2

ipfs-test:
	@echo "Running real IPFS integration test against $(IPFS_API_ADDR) ..."
	USE_REAL_IPFS=1 IPFS_API_ADDR=$(IPFS_API_ADDR) pytest -q tests/test_real_ipfs_integration.py

