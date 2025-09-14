.PHONY: help ipfs-test ipfs-check ipfs-docker-up \
	keystore-file-list keystore-file-rotate keystore-env-list keystore-env-rotate \
	contracts-compile contracts-node contracts-deploy contracts-deploy-local contracts-addresses \
	circuits-compile circuits-setup circuits-prove circuits-export-verifier circuits-clean circuits-all

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
	@echo "  contracts-compile    Compile Hardhat contracts"
	@echo "  contracts-node       Start a local Hardhat node"
	@echo "  contracts-deploy     Deploy to in-process Hardhat network (writes addresses)"
	@echo "  contracts-deploy-local Deploy to localhost Hardhat/Anvil (requires node)"
	@echo "  contracts-addresses  Print consolidated deployed addresses"
	@echo "  circuits-compile     Compile Circom circuits to R1CS/WASM"
	@echo "  circuits-setup       Groth16 setup (requires PTAU=path/to.ptau)"
	@echo "  circuits-prove       Generate witness/proof with optional INPUT=..."
	@echo "  circuits-export-verifier  Export Solidity verifier to contracts/src/RedactionVerifier_groth16.sol"
	@echo "  circuits-clean       Remove circuits/build artifacts"
	@echo "  circuits-all         Compile, setup, prove, and export verifier"

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


# -------------------------
# Contracts (Hardhat)
# -------------------------

CONTRACTS_DIR ?= contracts

contracts-compile:
	@cd $(CONTRACTS_DIR) && npx hardhat compile

contracts-node:
	@cd $(CONTRACTS_DIR) && npx hardhat node

contracts-deploy:
	@cd $(CONTRACTS_DIR) && npx hardhat run scripts/deploy.js

contracts-deploy-local:
	@cd $(CONTRACTS_DIR) && npx hardhat run scripts/deploy.js --network localhost

contracts-addresses:
	@cd $(CONTRACTS_DIR) && test -f deployed_addresses.json && cat deployed_addresses.json || echo "No deployed_addresses.json found"


# -------------------------
# Circuits (Circom + snarkjs)
# -------------------------

CIRCUITS_DIR ?= circuits
PTAU ?=
INPUT ?=

circuits-compile:
	@bash $(CIRCUITS_DIR)/scripts/compile.sh

circuits-setup:
	@PTAU=$(PTAU) bash $(CIRCUITS_DIR)/scripts/setup.sh

circuits-prove:
	@bash $(CIRCUITS_DIR)/scripts/prove.sh $(INPUT)

circuits-export-verifier:
	@bash $(CIRCUITS_DIR)/scripts/export-verifier.sh

circuits-clean:
	@bash $(CIRCUITS_DIR)/scripts/clean.sh

circuits-all: circuits-compile circuits-setup circuits-prove circuits-export-verifier
