.PHONY: help ipfs-test ipfs-check

IPFS_API_ADDR ?= /ip4/127.0.0.1/tcp/5001/http

help:
	@echo "Available targets:"
	@echo "  ipfs-test    Run real IPFS integration test (requires local daemon)"
	@echo "  ipfs-check   Query IPFS API version to verify connectivity"

ipfs-check:
	@echo "Checking IPFS API at $(IPFS_API_ADDR) ..."
	@python3 -c "import os, json; import ipfshttpclient as i; a=os.environ.get('IPFS_API_ADDR','/ip4/127.0.0.1/tcp/5001/http'); print(json.dumps(i.connect(a).version(), indent=2))"


ipfs-test:
	@echo "Running real IPFS integration test against $(IPFS_API_ADDR) ..."
	USE_REAL_IPFS=1 IPFS_API_ADDR=$(IPFS_API_ADDR) pytest -q tests/test_real_ipfs_integration.py



ipfs-docker-up:
	@bash scripts/ipfs_docker_up.sh
