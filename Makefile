.PHONY: help ipfs-test ipfs-check ipfs-docker-up \
	keystore-file-list keystore-file-rotate keystore-env-list keystore-env-rotate

IPFS_API_ADDR ?= /ip4/127.0.0.1/tcp/5001/http

help:
	@echo "Available targets:"
	@echo "  ipfs-test    Run real IPFS integration test (requires local daemon)"
	@echo "  ipfs-check   Query IPFS API version to verify connectivity"
	@echo "  ipfs-docker-up  Start local IPFS daemon via Docker Compose script"
	@echo "  keystore-file-list   List keys in file keystore (KEYSTORE, PASSPHRASE)"
	@echo "  keystore-file-rotate Rotate/generate key in file keystore (KEYSTORE, PASSPHRASE, NEW_KEY_B64)"
	@echo "  keystore-env-list    List keys for env provider"
	@echo "  keystore-env-rotate  Rotate/generate env key (NEW_KEY_B64, PRINT_EXPORTS=1)"

ipfs-check:
	@echo "Checking IPFS API at $(IPFS_API_ADDR) ..."
	@python3 -c "import os, json; import ipfshttpclient as i; a=os.environ.get('IPFS_API_ADDR','/ip4/127.0.0.1/tcp/5001/http'); print(json.dumps(i.connect(a).version(), indent=2))"


ipfs-test:
	@echo "Running real IPFS integration test against $(IPFS_API_ADDR) ..."
	USE_REAL_IPFS=1 IPFS_API_ADDR=$(IPFS_API_ADDR) pytest -q tests/test_real_ipfs_integration.py



ipfs-docker-up:
	@bash scripts/ipfs_docker_up.sh


# -------------------------
# Keystore helpers
# -------------------------

KEYSTORE ?= keystore.json
PASSPHRASE ?=
NEW_KEY_B64 ?=
PRINT_EXPORTS ?= 0

keystore-file-list:
	@python3 scripts/keystore_cli.py list --provider file --keystore "$(KEYSTORE)" $(if $(PASSPHRASE),--passphrase "$(PASSPHRASE)",)

keystore-file-rotate:
	@python3 scripts/keystore_cli.py rotate --provider file --keystore "$(KEYSTORE)" $(if $(PASSPHRASE),--passphrase "$(PASSPHRASE)",) $(if $(NEW_KEY_B64),--new-key-base64 "$(NEW_KEY_B64)",)

keystore-env-list:
	@python3 scripts/keystore_cli.py list --provider env

keystore-env-rotate:
	@python3 scripts/keystore_cli.py rotate --provider env $(if $(NEW_KEY_B64),--new-key-base64 "$(NEW_KEY_B64)",) $(if $(PRINT_EXPORTS),--print-exports,)
