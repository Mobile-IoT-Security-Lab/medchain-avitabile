# MedChain Project

[![Tests](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/tests.yml) ![Python Coverage](badges/python-coverage.svg) [![Contracts](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/contracts.yml/badge.svg?branch=main)](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/contracts.yml) ![Solidity Coverage](badges/solidity-coverage.svg)

This is a project for the Decentralized Systems course at the University of Genoa. Originally forked from the Redactable Blockchain Benchmarks repository, this project adds the support for smart contracts in the Ateniese implementation to implement a proof-of-concept for the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains". In particular, the MedChain project uses a medical use case to demonstrate the capabilities of redactable blockchains with smart contracts, focusing on patient data management and privacy compliance.

## Overview

This project focuses on my implementation of redactable blockchain with smart contract support:

- **My Implementation**: Chameleon hash-based redaction with complete smart contract support, SNARKs, proof-of-consistency, and medical use case implementation

My implementation has been significantly improved to support smart contracts and all features required by the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains".

## New Implementation: Complete Paper Implementation

### SNARKs Implementation (`ZK/SNARKs.py`)

The project now includes a complete zero-knowledge SNARKs implementation for privacy-preserving redaction operations:

- **ZKProof Structure**: Comprehensive proof system with commitments, nullifiers, and Merkle roots
- **SNARK Circuit**: Custom circuit for redaction consistency with 5 key constraints:
  - Original data integrity verification
  - Redacted data validity checks  
  - Authorization signature verification
  - Policy compliance validation
  - Merkle path consistency
- **Verifier System**: Robust verification with replay attack prevention and temporal validity
- **Integration**: Seamlessly integrated with the existing blockchain redaction system

### Proof-of-Consistency (`ZK/ProofOfConsistency.py`)

Advanced consistency verification system ensuring blockchain integrity after redaction:

- **Multiple Check Types**: Block integrity, hash chain, Merkle tree, smart contract state, transaction ordering
- **State Transition Verification**: Validates contract state changes during redaction operations
- **Merkle Tree Consistency**: Complete Merkle proof generation and verification
- **Hash Chain Verification**: Ensures blockchain integrity is maintained
- **Cryptographic Proofs**: Generates verifiable proofs for all consistency checks

### Medical Data Engine (`medical/MedicalRedactionEngine.py`)

Complete medical use case implementation with GDPR compliance:

- **Medical Data Contracts**: Solidity-compatible smart contracts for healthcare data
- **GDPR Compliance**: Full "Right to be Forgotten" implementation
- **Multi-Redaction Types**: DELETE, ANONYMIZE, and MODIFY operations
- **Role-Based Access**: ADMIN, REGULATOR, PHYSICIAN, RESEARCHER roles
- **SNARK Integration**: All redaction operations include zero-knowledge proofs
- **Audit Trail**: Comprehensive logging of all medical data operations

### IPFS Integration (`medical/MedicalDataIPFS.py`)

Distributed storage system with redaction capabilities:

- **Medical Dataset Management**: Complete dataset lifecycle with versioning
- **IPFS Client**: Simulated IPFS interface for testing and development
- **Dataset Generator**: Creates realistic medical datasets for testing
- **Redaction Support**: Implements "right to be forgotten" in distributed storage
- **Integrity Verification**: Ensures data consistency across IPFS network
- **Encryption Support**: Optional encryption for sensitive medical data

#### Dataset Encryption (AES‑GCM)

- When `IPFS_ENC_KEY` is set (base64‑encoded 16/24/32‑byte key), datasets uploaded via `IPFSMedicalDataManager.upload_dataset(..., encrypt=True)` are encrypted with AES‑GCM.
- The ciphertext is stored as an envelope JSON (no plaintext on IPFS):
  - `{ "v": 1, "enc": "AES-GCM", "nonce": <base64>, "ciphertext": <base64> }`
- Downloads automatically decrypt when the key is present; if missing, AES‑GCM content cannot be read.
- Fallback behavior (when no key): a simulated `ENCRYPTED:` prefix is used for backward compatibility.

Quick start (EnvKeyProvider)

- Generate a key and set env var (example: AES‑256):
  - `python - <<'PY'\nimport os, base64; print(base64.b64encode(os.urandom(32)).decode())\nPY`
  - Add to `.env`: `IPFS_ENC_KEY=<printed_base64>`
- Optional gateway config: `IPFS_GATEWAY_URL` (used by real IPFS adapter for links).

FileKeyProvider (keystore file)

- Store keys encrypted with scrypt + AES‑GCM and rotate safely.
- Example usage:
  - Create keystore with passphrase and first key:
    - Python:
      - `python - <<'PY'`
      - `from medical.key_provider import FileKeyProvider; prov=FileKeyProvider('keystore.json', passphrase='change-me'); print(prov.rotate())`
      - `PY`
  - Use with the manager:
    - `from medical.MedicalDataIPFS import IPFSMedicalDataManager, FakeIPFSClient`
    - `from medical.key_provider import FileKeyProvider`
    - `prov=FileKeyProvider('keystore.json', passphrase='change-me')`
    - `mgr=IPFSMedicalDataManager(FakeIPFSClient(), key_provider=prov)`
  - Rotate key later (creates new version and marks active): `prov.rotate()`
  - CLI helper (inside repo):
    - Rotate: `python scripts/keystore_cli.py rotate --provider file --keystore keystore.json --passphrase 'change-me'`
    - List:   `python scripts/keystore_cli.py list   --provider file --keystore keystore.json --passphrase 'change-me'`
  - Historical decryption: manager resolves by `kid` embedded in envelopes, so old datasets remain decryptable even after rotation.

Key IDs and redaction by erasure

- Every envelope includes a `kid` (key id) derived from the AES key.
- Rotation creates new keys while preserving old ones for decryption (FileKeyProvider) or in an env-based pool (EnvKeyProvider via `IPFS_ENC_KEYS`).
- A practical “redaction by erasure” pattern: rotate to a new key, unpin old ciphertext (allow GC), and remove the old key material from the keystore/pool so old data becomes undecipherable.

### Complete Demo System (`demo/medchain_demo.py`)

Comprehensive demonstration of all implemented features:

#### Demo Phases

1. **Dataset Creation**: Generate and upload medical datasets to IPFS
2. **Blockchain Integration**: Store medical records in smart contracts
3. **Access Control**: Demonstrate querying with role-based permissions
4. **GDPR Implementation**: Complete "Right to be Forgotten" workflow
5. **SNARK Verification**: Generate and verify zero-knowledge proofs
6. **Audit & Compliance**: Comprehensive audit trails and compliance reporting
7. **Advanced Scenarios**: Batch operations, emergency redaction, selective modification

#### Key Features Demonstrated

- Complete GDPR Article 17 compliance
- HIPAA-compliant data anonymization
- Zero-knowledge proof generation and verification
- Proof-of-consistency for all operations
- Multi-signature approval workflows
- Immutable audit trails
- Distributed storage with redaction
- Smart contract state management

Backend Toggle (EVM vs. Simulated)

- The medical redaction engine supports a pluggable backend for redaction requests/approvals:
  - `REDACTION_BACKEND=SIMULATED` (default): all logic runs in Python; EVM is used only if the demo explicitly calls it.
  - `REDACTION_BACKEND=EVM`: the engine mirrors requests and approvals to the EVM via the adapter for audit/events.
- To run with EVM backend (requires local devnet and compiled artifacts):
  1) Start a local node: `make contracts-node` (or run your own Hardhat/Anvil node on `localhost:8545`).
  2) In a second shell, deploy and write addresses: `make contracts-deploy-local`.
  3) Run the demo with env:
     - `USE_REAL_EVM=1 REDACTION_BACKEND=EVM python -m demo.medchain_demo`
  4) The demo will auto-load the MedicalDataManager address from `contracts/deployments/<chainId>/` or `contracts/deployed_addresses.json`.

### Technical Improvements

The implementation includes several technical advances:

- **Chameleon Hash Integration**: My chameleon hash functions with secret sharing
- **Multi-Party Redaction**: Support for collaborative redaction operations
- **Policy Engine**: Configurable redaction policies with automatic enforcement
- **Cryptographic Security**: Military-grade cryptographic primitives
- **Performance Optimization**: Efficient proof generation and verification
- **Scalability**: Designed for enterprise-scale medical data management

### Testing and Validation

Comprehensive test suite covering all components:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation  
- **Performance Tests**: Scalability and efficiency validation
- **Security Tests**: Cryptographic proof verification
- **Compliance Tests**: GDPR and HIPAA compliance validation
rm -rf docs

#### VS Code Test Integration

The project includes full VS Code pytest integration with convenient test runners:

```bash
# Quick test runner (recommended)
./run_tests.py tests/test_adapter_interfaces.py -v

# Comprehensive test suite (matches VS Code execution)
./run_comprehensive_tests.sh

# Setup development environment with VS Code support
./setup_dev.sh
```

**VS Code Users**: Tests run seamlessly in VS Code's Python Test Explorer without additional configuration.

For detailed testing documentation, see [`docs/VSCODE_TEST_FIX.md`](docs/VSCODE_TEST_FIX.md).

## My Implementation Features

- **Smart Contract Support** (Models/SmartContract.py): Full lifecycle management with deployment, execution, and state management for audit, privacy compliance, and general-purpose contracts
- **Role-Based Access Control**: Five permission levels from OBSERVER (read-only) to ADMIN (full system control) with specific capabilities for each role
- **Advanced Redaction Types**: DELETE (complete removal), MODIFY (selective editing), and ANONYMIZE (privacy protection) with multi-signature approval workflows
- **Privacy & Compliance**: Built-in GDPR, HIPAA, and SOX compliance with configurable data retention policies and automated privacy level enforcement
- **Transaction Distribution** (Models/Transaction.py): Optimized mix of transfers (80%), contract calls (10%), deployments (5%), and redaction requests (5%)
- **Test suite**.
- **Improved scripts**: Models/Transaction.py, Models/Bitcoin/Node.py, Models/Block.py, Models/Bitcoin/BlockCommit.py, InputsConfig.py, Main.py, Statistics.py

## Getting Started

### Prerequisites

**System Requirements:**

- **Python**: 3.8+ (for blockchain simulation and medical engine)
- **Node.js**: 16.0+ (for smart contracts and SNARK circuits)
- **npm**: 8.0+ (for dependency management)

### Quick Start

**New to MedChain?** See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) for a fast setup guide.

**Need Node.js details?** Check [`docs/NODEJS_REQUIREMENTS.md`](docs/NODEJS_REQUIREMENTS.md) for comprehensive Node.js setup instructions.

### One-Command Setup

```bash
git clone <your-repo-url>
cd medchain-avitabile
make setup
```

## Installation

### 1. Python Dependencies

```bash
# Clone the repository
git clone [repository-url]
cd medchain-avitabile

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Node.js Dependencies

```bash
# Install global dependencies (required for real SNARK proofs)
npm install -g snarkjs@^0.7.5

# Install circom (circuit compiler) - Download from GitHub releases
# For Linux x64:
wget -O /tmp/circom https://github.com/iden3/circom/releases/latest/download/circom-linux-amd64
sudo mv /tmp/circom /usr/local/bin/circom
sudo chmod +x /usr/local/bin/circom

# Or install via cargo (requires Rust):
# cargo install circom

# Install project dependencies
npm install

# Install contract dependencies
cd contracts && npm install && cd ..
```

### 3. Build Circuits (Optional - for real SNARK proofs)

```bash
# Build all circuits and generate proving keys
npm run build-circuits

# Or manually:
cd circuits
chmod +x scripts/*.sh
./scripts/compile.sh    # Compile .circom to .wasm and .r1cs
./scripts/setup.sh      # Generate proving keys (requires Powers of Tau)
./scripts/prove.sh      # Generate test proof
./scripts/export-verifier.sh  # Export Solidity verifier
```

### 4. Compile Smart Contracts

```bash
# Build all smart contracts
npm run build-contracts

# Or manually:
cd contracts
npm run compile
```

## Usage

### Basic Simulation (No Node.js required)

```bash
# Run basic blockchain simulation with simulated SNARKs
python Main.py

# Fast preview mode
TESTING_MODE=1 DRY_RUN=1 python Main.py
```

### Full Demo with Real SNARKs

```bash
# Run with real SNARK proof generation (requires snarkjs)
USE_REAL_SNARK=1 python -m demo.medchain_demo

# Run medical redaction demo
python -m demo.medical_redaction_demo
```

### NPM Scripts Reference

The project includes several npm scripts for common tasks:

```bash
# Setup and Installation
npm run setup                # Complete setup (global deps + install)
npm run install-global      # Install global dependencies only

# Circuit Development
npm run build-circuits       # Compile circuits and generate keys
npm run prove-circuits      # Generate test proofs
npm run export-verifier     # Export Solidity verifier

# Smart Contract Development  
npm run build-contracts     # Compile Solidity contracts
npm run test-contracts      # Run contract tests
npm run deploy-contracts    # Deploy to local network

# Development Workflow
npm run dev                 # Build circuits + contracts
npm run test               # Run all tests (contracts + Python)

# Demos
npm run demo               # Main medical demo
npm run demo-medical       # Medical redaction demo
npm run demo-ipfs         # IPFS integration demo
npm run demo-snark        # SNARK proof demo
```

### Environment Configuration

The project supports various environment variables for configuration:

#### SNARK Configuration

```bash
# Enable real SNARK proofs (requires snarkjs and compiled circuits)
USE_REAL_SNARK=1

# Circuit directory (default: circuits)
CIRCUITS_DIR=circuits

# Pre-built proof paths (for testing)
GROTH16_PROOF_JSON=circuits/build/proof.json
GROTH16_PUBLIC_JSON=circuits/build/public.json
```

#### EVM Configuration

```bash
# Enable real EVM integration (requires local blockchain)
USE_REAL_EVM=1

# Blockchain connection
WEB3_PROVIDER_URI=http://localhost:8545
EVM_CHAIN_ID=31337

# Contract addresses (auto-populated by deployment)
MEDICAL_CONTRACT_ADDRESS=0x...
VERIFIER_CONTRACT_ADDRESS=0x...
```

#### IPFS Configuration

```bash
# Enable real IPFS (requires IPFS node)
USE_REAL_IPFS=1

# IPFS connection
IPFS_API_URL=http://localhost:5001
IPFS_GATEWAY_URL=http://localhost:8080

# Encryption key for medical data (base64-encoded 16/24/32 bytes)
IPFS_ENC_KEY=base64encodedkey...
```

#### Testing Configuration

```bash
# Enable testing mode (smaller datasets, faster execution)
TESTING_MODE=1

# Dry run mode (no actual execution)
DRY_RUN=1

# Backend selection
REDACTION_BACKEND=SIMULATED  # or EVM
```

### Dependency Management

#### Required Global Dependencies

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **snarkjs** | ^0.7.5 | SNARK proof generation | `npm install -g snarkjs` |
| **circom** | latest | Circuit compilation | Download from [releases](https://github.com/iden3/circom/releases) |

#### Development Dependencies

The project uses npm workspaces to manage dependencies:

- **Root package.json**: Global scripts and snarkjs
- **contracts/package.json**: Hardhat, Solidity tools, contract testing

#### Manual Installation (Alternative)

If automatic installation fails, you can install dependencies manually:

```bash
# 1. Install snarkjs globally
npm install -g snarkjs@0.7.5

# 2. Install circom (choose one method):

# Method A: Download binary (Linux x64)
wget https://github.com/iden3/circom/releases/latest/download/circom-linux-amd64 -O circom
sudo mv circom /usr/local/bin/circom
sudo chmod +x /usr/local/bin/circom

# Method B: Build from source (requires Rust)
git clone https://github.com/iden3/circom.git
cd circom
cargo build --release
sudo cp target/release/circom /usr/local/bin/

# Method C: Install via package manager (Ubuntu/Debian)
# Note: May not be latest version
sudo apt-get install circom

# 3. Verify installation
snarkjs --version  # Should show v0.7.5
circom --version   # Should show version info
```

### MedChain Implementation

```bash
# Clone the repository
git clone [repository-url]

# Install dependencies
pip install -r requirements.txt

# Run my implementation
python Main.py
```

### Complete MedChain Demo

```bash
# Install dependencies (includes SNARK and IPFS support)
pip install -r requirements.txt

# Run the complete MedChain demo
python -m demo.medchain_demo

# Run individual component demos
python ZK/SNARKs.py
python ZK/ProofOfConsistency.py
python -m demo.medical_redaction_demo
python -m demo.ipfs_demo
python -m demo.redactable_blockchain_demo
python -m demo.avitabile_redaction_demo
python -m demo.avitabile_consistency_demo
python -m demo.avitabile_censored_ipfs_pipeline
```

## Experimental Framework

The simulations in this project are conducted using the [BlockSim simulator](https://github.com/maher243/BlockSim). BlockSim is an open-source simulator specifically designed for blockchain systems. It provides intuitive simulation constructs and allows for customization to support multiple blockchain design and deployment scenarios.

### Framework Features

The implementation extends BlockSim with:

- **Smart Contract Execution Engine**: Simulated smart contract deployment and execution
- **Permission Management System**: Role-based access control simulation
- **Privacy Policy Enforcement**: Automated privacy compliance checking
- **Multi-Signature Governance**: Simulated approval workflows for redaction requests
- **Performance Monitoring**: Advanced metrics collection and analysis

## Configuration Examples

### Basic Configuration

```python
# InputsConfig.py
Nodes = 20                    # Number of nodes
Tn = 5                       # Transactions per second
Binterval = 10               # Block interval in seconds
hasRedact = True             # Enable redaction
redactionProbability = 0.1   # 10% of blocks may be redacted
```

### My Configuration

```python
# InputsConfig.py
hasSmartContracts = True             # Enable smart contracts
hasPermissions = True                # Enable role-based permissions
hasPrivacyLevels = True              # Enable privacy classification
requireRedactionApproval = True      # Require multi-sig approvals
minRedactionApprovals = 2            # Minimum required approvals

# Smart contract parameters
contractDeploymentRate = 0.05        # 5% of transactions are deployments
contractCallRate = 0.10              # 10% are contract calls

# Privacy and compliance
dataRetentionPeriod = 86400 * 365    # 1 year retention period
privacyComplianceMode = "GDPR"       # Compliance framework

# Node role assignments
NODE_ROLES = {
    1: "ADMIN",      # System administrator
    2: "REGULATOR",  # Compliance officer
    3: "MINER",      # Block producer
    4: "USER"        # Regular participant
}

# Redaction policies
REDACTION_POLICIES = [
    {
        "policy_id": "GDPR_COMPLIANCE",
        "policy_type": "DELETE",
        "authorized_roles": ["ADMIN", "REGULATOR"],
        "min_approvals": 2,
        "time_lock": 86400
    }
]
```

## References

- Gennaro Avitabile, Vincenzo Botta, Daniele Friolo and Ivan Visconti "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains"
- [Deuber, D., Magri, B., & Thyagarajan, S. A. K. (2019, May). Redactable blockchain in the permissionless setting. In 2019 IEEE Symposium on Security and Privacy (SP) (pp. 124-138). IEEE.](https://ieeexplore.ieee.org/abstract/document/8835372)
- [Ateniese, G., Magri, B., Venturi, D., & Andrade, E. (2017, April). Redactable blockchain–or–rewriting history in bitcoin and friends. In 2017 IEEE European symposium on security and privacy (EuroS&P) (pp. 111-126). IEEE.](https://ieeexplore.ieee.org/abstract/document/7961975/)
- [Puddu, I., Dmitrienko, A., & Capkun, S. (2017). $\mu $ chain: How to Forget without Hard Forks. Cryptology ePrint Archive.](https://eprint.iacr.org/2017/106)
- [Botta, V., Iovino, V., & Visconti, I. (2022). Towards Data Redaction in Bitcoin. IEEE Transactions on Network and Service Management, 19(4), 3872-3883.](https://doi.org/10.1109/TNSM.2022.3214279)

## Codebase Map

- Overview
  - Python simulation of a redactable, permissioned blockchain (Bitcoin‑like) with smart contracts, role‑based redaction governance, and a medical/IPFS demo.
  - Core redaction uses chameleon hashes (Ateniese‑style). Smart contracts, SNARKs, proof‑of‑consistency, and IPFS are simulated to support the Avitabile paper use case.

- How to Run
  - Install deps: `pip install -r requirements.txt`
  - Simulator: `python Main.py`  (fast preview: `TESTING_MODE=1 DRY_RUN=1 python Main.py`)
  - Demos: `python -m demo.medchain_demo`, `python ZK/SNARKs.py`, `python ZK/ProofOfConsistency.py`, `python -m demo.redactable_blockchain_demo`, `python -m demo.avitabile_*`, `python -m demo.medical_redaction_demo`, `python -m demo.ipfs_demo`
  - Tests: `pytest -q tests`

- Configuration (`InputsConfig.py`)
  - Central toggles: `hasRedact`, `hasSmartContracts`, `hasPermissions`, `minRedactionApprovals`, `REDACTION_POLICIES`, transaction mix, network size.
  - Enable testing mode via `InputsConfig.initialize(testing_mode=True)` or env var `TESTING_MODE=1`.

- Structure
  - Core sim: `Main.py`, `Event.py`, `Scheduler.py`, `Models/Bitcoin/*`, `Models/Transaction.py`, `Models/Block.py`, `Statistics.py`.
  - Redaction primitives: `CH/ChameleonHash.py`, `CH/SecretSharing.py`.
  - Smart contracts (simulated): `Models/SmartContract.py` (contract model, execution engine, permissions, policies).
  - ZK & consistency (simulated): `ZK/SNARKs.py`, `ZK/ProofOfConsistency.py`.
  - Medical/IPFS (simulated): `medical/MedicalRedactionEngine.py`, `medical/MedicalDataIPFS.py`.
  - Demos: `demo/*`.  Tests: `tests/*`.  Docs: `docs/*`.

- Redaction Flow (high level)
  - Modify/delete a historical tx → recompute message (tx list + prev) → forge new randomness `r` with trapdoor so the chameleon hash stays consistent → update block id and propagate; governance via role‑based approvals.

- Known Limitations/Gaps
  - SNARKs, contract execution, and IPFS are proof‑of‑concept simulations (not production crypto/EVM/IPFS).
  - Chameleon‑hash parameters and keys are fixed for demo usage.
  - Medical contract code strings contain TODO placeholders; policy checks can be further wired end‑to‑end in the redaction request path.

## Developer Guide

### Core Concepts

#### Chameleon Hash Redaction (Ateniese)

The blockchain uses chameleon hashes to allow redaction without breaking the chain:

```tex
CH(m, r) = g^m · PK^r mod p
```

**How redaction works:**

1. Choose a historical block/transaction to modify
2. Compute new message m2 (updated transaction list + previous hash)
3. Use trapdoor to forge new randomness: `r2 = forge(SK, m1, r1, m2)`
4. Result: `CH(m1, r1) = CH(m2, r2)` - hash stays the same!
5. Update block ID and propagate - chain remains valid

**Implementation:** `CH/ChameleonHash.py`, `Models/Bitcoin/BlockCommit.py`

#### Smart Contract Redaction (Avitabile)

Extends Ateniese with:

- Smart contract governance for redactions
- Zero-knowledge SNARK proofs
- Proof-of-consistency verification
- Role-based permissions (ADMIN, REGULATOR, MINER, USER, OBSERVER)
- Medical data use case with GDPR compliance

### Structure Overview

#### Core Simulation

- `Main.py`: Entry point, runs blockchain simulation, deploys example contracts
- `InputsConfig.py`: All parameters (nodes, block intervals, transaction mix, policies, testing mode)
- `Event.py` + `Scheduler.py`: Discrete-event engine for block creation/propagation
- `Statistics.py`: Collects metrics (blocks, transactions, redactions, contracts)

#### Blockchain Model

- `Models/Block.py`: Block structure with transactions, chameleon hash randomness `r`, smart contracts, redaction metadata
- `Models/Transaction.py`: Transaction types (TRANSFER, CONTRACT_CALL, CONTRACT_DEPLOY, REDACTION_REQUEST)
- `Models/Bitcoin/Node.py`: Nodes with hashrate, roles/permissions, contract deployment, redaction voting
- `Models/Bitcoin/BlockCommit.py`: **Core of the system** - mining, propagation, redaction execution using chameleon hash forge

#### Redaction Primitives

- `CH/ChameleonHash.py`: Chameleon hash with trapdoor (centralized and multi-party variants)
- `CH/SecretSharing.py`: Hooks for multi-party secret sharing (simulated)

#### Smart Contracts (Simulated)

- `Models/SmartContract.py`: In-memory contract model, execution engine (gas simulation), permission manager, redaction policies

#### Zero-Knowledge & Consistency (Simulated)

- `ZK/SNARKs.py`: SNARK-like proof structure, circuit scaffolding, commitment/nullifier, replay protection
- `ZK/ProofOfConsistency.py`: Proof generators/verifiers for block integrity, Merkle trees, hash chain, contract state transitions

#### Medical Use Case + IPFS

- `medical/MedicalRedactionEngine.py`: Medical data contracts, redaction requests with SNARK generation, approval workflow, audit trail
- `medical/MedicalDataIPFS.py`: Simulated IPFS client (stores to `/tmp/fake_ipfs`), dataset generator, patient mapping, versioned redaction
- `demo/medchain_demo.py`: End-to-end demo (dataset → storage → access → GDPR deletion → proofs → audit)

### Run Modes

#### Standard Simulation

```bash
pip install -r requirements.txt
python Main.py
```

Tuning: Edit `InputsConfig.py` (e.g., `NUM_NODES`, `hasSmartContracts`, `hasPermissions`, `REDACTION_POLICIES`)

#### Testing Mode (Faster, Smaller)

```bash
# Via environment variable
TESTING_MODE=1 python Main.py

# Or in code
InputsConfig.initialize(testing_mode=True)
```

Effects: Fewer nodes, faster block interval, higher tx rates, richer policy set

#### Preview Configuration

```bash
TESTING_MODE=1 DRY_RUN=1 python Main.py
```

Prints configuration and exits without running simulation

#### MedChain Demo (Full Stack)

```bash
python -m demo.medchain_demo
```

Phases: dataset → store in contract → access control → GDPR delete → SNARK + consistency proofs → audit reports → advanced scenarios

#### Component Demos

```bash
python ZK/SNARKs.py                              # SNARK proof system
python ZK/ProofOfConsistency.py                  # Consistency verification
python -m demo.medical_redaction_demo            # Medical redaction
python -m demo.ipfs_demo                         # IPFS integration
python -m demo.redactable_blockchain_demo        # Basic chameleon hash
python -m demo.avitabile_redaction_demo          # Avitabile paper demo
python -m demo.avitabile_consistency_demo        # Consistency proofs demo
python -m demo.avitabile_censored_ipfs_pipeline  # Full censored pipeline
```

### Key Workflows

#### Redaction Workflow

1. Request created by authorized role (ADMIN/REGULATOR)
2. Check redaction policy (min approvals, time locks, required roles)
3. Multi-party voting among approvers
4. On quorum → Generate SNARK proof
5. Generate consistency proofs (Merkle, hash chain, contract state)
6. Recompute message m2 (updated tx list + previous hash)
7. Forge new randomness: `r2 = forge(SK, m1, r1, m2)`
8. Update block ID, verify `CH(m1, r1) = CH(m2, r2)`
9. Add redaction metadata and audit trail
10. Propagate to network

#### Governance & Permissions

- Node roles: ADMIN, REGULATOR, MINER, USER, OBSERVER
- Permissions configured in `InputsConfig.py`: `NODE_ROLES`, `minRedactionApprovals`, `REDACTION_POLICIES`
- Voting simulated in `BlockCommit.process_redaction_requests()`
- Policy checks in `BlockCommit.check_redaction_policy()`

#### Smart Contract Lifecycle

1. Contract creation (ADMIN role)
2. Deploy via `Node.deploy_contract()` → `CONTRACT_DEPLOY` transaction
3. Store in `block.smart_contracts[]`
4. Execution via `ContractExecutionEngine` (simulated gas + logs)
5. State updates tracked in `block.get_smart_contract_state()`
6. Redaction consistency verified via `ZK/ProofOfConsistency.py`

### Configuration Tips

#### Experiment Tuning (`InputsConfig.py`)

```python
# Network size
NUM_NODES = 1000              # Production
NUM_NODES = 50                # Testing

# Block generation
Binterval = 600               # 10 minutes (production)
Binterval = 300               # 5 minutes (testing)

# Transactions
Tn = 5                        # Tx per second (production)
Tn = 10                       # Higher rate (testing)

# Redaction settings
hasRedact = True
minRedactionApprovals = 2     # Quorum threshold
redactRuns = 10               # Number of redaction operations

# Smart contracts
hasSmartContracts = True
hasPermissions = True

# Transaction mix
TRANSACTION_TYPE_DISTRIBUTION = {
    "TRANSFER": 0.80,          # 80% transfers
    "CONTRACT_CALL": 0.10,     # 10% calls
    "CONTRACT_DEPLOY": 0.05,   # 5% deployments
    "REDACTION_REQUEST": 0.05  # 5% redaction requests
}
```

#### Environment Variables

##### Core Flags

```bash
TESTING_MODE=1          # Enable testing mode (1/true/yes/on)
DRY_RUN=1              # Print config and exit
```

##### IPFS Encryption

```bash
# Generate AES-256 key
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"

# Set in .env
IPFS_ENC_KEY=<base64_key>              # AES key (16/24/32 bytes)
IPFS_ENC_KEY_ID=<kid>                  # Active key ID (optional)
IPFS_ENC_KEYS='{"kid1":"key1",...}'    # Key pool JSON (optional)
IPFS_GATEWAY_URL=http://localhost:8080
```

##### Backend Selection

```bash
USE_REAL_IPFS=1        # Use actual IPFS daemon
USE_REAL_EVM=1         # Use Hardhat/Anvil
USE_REAL_SNARK=1       # Use snarkjs for proofs
REDACTION_BACKEND=EVM  # or SIMULATED
```

### Testing

#### Run Tests

```bash
# All tests
pytest tests/

# Specific markers
pytest -m unit                    # Fast unit tests
pytest -m integration             # Integration tests
pytest -m "not slow"              # Skip slow tests

# Coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_consistency_system.py -v
```

#### Test Structure

- `tests/conftest.py`: Pytest configuration, fixtures
- `tests/integration_test.py`: Full integration suite
- `tests/performance_test.py`: Benchmarks
- `tests/test_*`: Component-specific tests

All tests should pass for valid benchmark runs.

### Key Providers and Rotation

#### Environment-Based (EnvKeyProvider)

```bash
# Single key
export IPFS_ENC_KEY=<base64>

# Multiple keys with rotation
export IPFS_ENC_KEYS='{"kid1":"key1_b64","kid2":"key2_b64"}'
export IPFS_ENC_KEY_ID=kid2  # Active key

# Rotate
python scripts/keystore_cli.py rotate --provider env --print-exports
```

#### File-Based (FileKeyProvider)

```bash
# Create keystore
python scripts/keystore_cli.py rotate \
  --provider file \
  --keystore keystore.json \
  --passphrase 'secure-password'

# List keys
python scripts/keystore_cli.py list \
  --provider file \
  --keystore keystore.json \
  --passphrase 'secure-password'

# Use in code
from medical.key_provider import FileKeyProvider
from medical.MedicalDataIPFS import IPFSMedicalDataManager, FakeIPFSClient

prov = FileKeyProvider('keystore.json', passphrase='secure-password')
mgr = IPFSMedicalDataManager(FakeIPFSClient(), key_provider=prov)
```

### Real IPFS Integration

#### Setup Local IPFS

```bash
# Start IPFS daemon (or use Docker)
ipfs daemon

# Or use Docker
make ipfs-docker-up

# Check connection
make ipfs-check
```

#### Configure Real IPFS

```bash
# In .env
USE_REAL_IPFS=1
IPFS_API_ADDR=/ip4/127.0.0.1/tcp/5001/http
IPFS_API_URL=http://127.0.0.1:5001
IPFS_GATEWAY_URL=http://127.0.0.1:8080/ipfs
```

#### Example Usage

```python
# Auto-detects real vs simulated based on USE_REAL_IPFS
from adapters.ipfs import get_ipfs_client
from medical.MedicalDataIPFS import IPFSMedicalDataManager

client = get_ipfs_client()  # Returns RealIPFSClient or FakeIPFSClient
mgr = IPFSMedicalDataManager(client)
```

### Makefile Targets

```bash
make setup              # Complete setup (npm + python)
make setup-npm          # Install Node.js dependencies
make setup-python       # Install Python dependencies

make ipfs-docker-up     # Start IPFS daemon
make ipfs-check         # Verify IPFS connection
make ipfs-test          # Run IPFS integration tests

make contracts-compile  # Compile smart contracts
make contracts-node     # Start local Hardhat node
make contracts-deploy   # Deploy contracts

make circuits-compile   # Compile circom circuits
make circuits-all       # Full circuit workflow

make keystore-file-list # List keystore keys
make keystore-file-rotate # Rotate keystore key
```

### Known Limitations

#### Simulations (Not Production)

- **SNARKs**: Proof-of-concept, not real cryptographic proofs
- **Smart Contracts**: In-memory simulation, not real EVM
- **IPFS**: Simulated client (unless `USE_REAL_IPFS=1`)
- **Chameleon Hash**: Fixed demo parameters, not production-ready

#### Implementation Gaps

- `BlockCommit.check_redaction_policy()` exists but not fully wired to request flow
- Medical contract Solidity code has TODO placeholders (illustrative only)
- Multi-party secret sharing is stubbed, not fully implemented
- Policy enforcement could be more granular

#### Not Included

- Production cryptographic security
- Real EVM bytecode execution
- Actual network layer (P2P)
- Persistent storage beyond simulation runs

### Contributing

#### Development Workflow

1. Keep changes minimal and focused
2. Run tests before committing: `pytest tests/`
3. Update docs if changing public interfaces
4. Follow existing code patterns
5. Test in both normal and testing modes

#### Code Organization

- Keep simulation logic in `Models/Bitcoin/`
- Cryptographic primitives in `CH/` and `ZK/`
- Use case implementations in `medical/`
- Demos in `demo/`
- Tests in `tests/`
