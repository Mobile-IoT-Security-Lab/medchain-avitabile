# Developer Guide

This project is a **Python simulation** of a redactable, permissioned blockchain (Bitcoin-like) with smart contracts, role-based governance, and a medical data use case. It implements two key papers:

1. **Ateniese et al.** - "Redactable Blockchain – or – Rewriting History in Bitcoin and Friends" (chameleon hash foundation)
2. **Avitabile et al.** - "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" (smart contracts + ZK proofs)

## Core Concepts

### Chameleon Hash Redaction (Ateniese)

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

### Smart Contract Redaction (Avitabile)

Extends Ateniese with:

- Smart contract governance for redactions
- Zero-knowledge SNARK proofs
- Proof-of-consistency verification
- Role-based permissions (ADMIN, REGULATOR, MINER, USER, OBSERVER)
- Medical data use case with GDPR compliance

## Structure Overview

### Core Simulation

- `Main.py`: Entry point, runs blockchain simulation, deploys example contracts
- `InputsConfig.py`: All parameters (nodes, block intervals, transaction mix, policies, testing mode)
- `Event.py` + `Scheduler.py`: Discrete-event engine for block creation/propagation
- `Statistics.py`: Collects metrics (blocks, transactions, redactions, contracts)

### Blockchain Model

- `Models/Block.py`: Block structure with transactions, chameleon hash randomness `r`, smart contracts, redaction metadata
- `Models/Transaction.py`: Transaction types (TRANSFER, CONTRACT_CALL, CONTRACT_DEPLOY, REDACTION_REQUEST)
- `Models/Bitcoin/Node.py`: Nodes with hashrate, roles/permissions, contract deployment, redaction voting
- `Models/Bitcoin/BlockCommit.py`: **Core of the system** - mining, propagation, redaction execution using chameleon hash forge

### Redaction Primitives

- `CH/ChameleonHash.py`: Chameleon hash with trapdoor (centralized and multi-party variants)
- `CH/SecretSharing.py`: Hooks for multi-party secret sharing (simulated)

### Smart Contracts (Simulated)

- `Models/SmartContract.py`: In-memory contract model, execution engine (gas simulation), permission manager, redaction policies

### Zero-Knowledge & Consistency (Simulated)

- `ZK/SNARKs.py`: SNARK-like proof structure, circuit scaffolding, commitment/nullifier, replay protection
- `ZK/ProofOfConsistency.py`: Proof generators/verifiers for block integrity, Merkle trees, hash chain, contract state transitions

### Medical Use Case + IPFS

- `medical/MedicalRedactionEngine.py`: Medical data contracts, redaction requests with SNARK generation, approval workflow, audit trail
- `medical/MedicalDataIPFS.py`: Simulated IPFS client (stores to `/tmp/fake_ipfs`), dataset generator, patient mapping, versioned redaction
- `demo/medchain_demo.py`: End-to-end demo (dataset → storage → access → GDPR deletion → proofs → audit)

## Run Modes

### Standard Simulation

```bash
pip install -r requirements.txt
python Main.py
```

Tuning: Edit `InputsConfig.py` (e.g., `NUM_NODES`, `hasSmartContracts`, `hasPermissions`, `REDACTION_POLICIES`)

### Testing Mode (Faster, Smaller)

```bash
# Via environment variable
TESTING_MODE=1 python Main.py

# Or in code
InputsConfig.initialize(testing_mode=True)
```

Effects: Fewer nodes, faster block interval, higher tx rates, richer policy set

### Preview Configuration

```bash
TESTING_MODE=1 DRY_RUN=1 python Main.py
```

Prints configuration and exits without running simulation

### MedChain Demo (Full Stack)

```bash
python -m demo.medchain_demo
```

Phases: dataset → store in contract → access control → GDPR delete → SNARK + consistency proofs → audit reports → advanced scenarios

### Component Demos

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

## Key Workflows

### Redaction Workflow

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

### Governance & Permissions

- Node roles: ADMIN, REGULATOR, MINER, USER, OBSERVER
- Permissions configured in `InputsConfig.py`: `NODE_ROLES`, `minRedactionApprovals`, `REDACTION_POLICIES`
- Voting simulated in `BlockCommit.process_redaction_requests()`
- Policy checks in `BlockCommit.check_redaction_policy()`

### Smart Contract Lifecycle

1. Contract creation (ADMIN role)
2. Deploy via `Node.deploy_contract()` → `CONTRACT_DEPLOY` transaction
3. Store in `block.smart_contracts[]`
4. Execution via `ContractExecutionEngine` (simulated gas + logs)
5. State updates tracked in `block.get_smart_contract_state()`
6. Redaction consistency verified via `ZK/ProofOfConsistency.py`

## Configuration Tips

### Experiment Tuning (`InputsConfig.py`)

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

### Environment Variables

#### Core Flags

```bash
TESTING_MODE=1          # Enable testing mode (1/true/yes/on)
DRY_RUN=1              # Print config and exit
```

#### IPFS Encryption

```bash
# Generate AES-256 key
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"

# Set in .env
IPFS_ENC_KEY=<base64_key>              # AES key (16/24/32 bytes)
IPFS_ENC_KEY_ID=<kid>                  # Active key ID (optional)
IPFS_ENC_KEYS='{"kid1":"key1",...}'    # Key pool JSON (optional)
IPFS_GATEWAY_URL=http://localhost:8080
```

#### Backend Selection

```bash
USE_REAL_IPFS=1        # Use actual IPFS daemon
USE_REAL_EVM=1         # Use Hardhat/Anvil
USE_REAL_SNARK=1       # Use snarkjs for proofs
REDACTION_BACKEND=EVM  # or SIMULATED
```

## Testing

### Run Tests

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

### Test Structure

- `tests/conftest.py`: Pytest configuration, fixtures
- `tests/integration_test.py`: Full integration suite
- `tests/performance_test.py`: Benchmarks
- `tests/test_*`: Component-specific tests

All tests should pass for valid benchmark runs.

## Key Providers and Rotation

### Environment-Based (EnvKeyProvider)

```bash
# Single key
export IPFS_ENC_KEY=<base64>

# Multiple keys with rotation
export IPFS_ENC_KEYS='{"kid1":"key1_b64","kid2":"key2_b64"}'
export IPFS_ENC_KEY_ID=kid2  # Active key

# Rotate
python scripts/keystore_cli.py rotate --provider env --print-exports
```

### File-Based (FileKeyProvider)

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

## Real IPFS Integration

### Setup Local IPFS

```bash
# Start IPFS daemon (or use Docker)
ipfs daemon

# Or use Docker
make ipfs-docker-up

# Check connection
make ipfs-check
```

### Configure Real IPFS

```bash
# In .env
USE_REAL_IPFS=1
IPFS_API_ADDR=/ip4/127.0.0.1/tcp/5001/http
IPFS_API_URL=http://127.0.0.1:5001
IPFS_GATEWAY_URL=http://127.0.0.1:8080/ipfs
```

### Usage

```python
# Auto-detects real vs simulated based on USE_REAL_IPFS
from adapters.ipfs import get_ipfs_client
from medical.MedicalDataIPFS import IPFSMedicalDataManager

client = get_ipfs_client()  # Returns RealIPFSClient or FakeIPFSClient
mgr = IPFSMedicalDataManager(client)
```

## Makefile Targets

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

## Known Limitations

### Simulations (Not Production)

- **SNARKs**: Proof-of-concept, not real cryptographic proofs
- **Smart Contracts**: In-memory simulation, not real EVM
- **IPFS**: Simulated client (unless `USE_REAL_IPFS=1`)
- **Chameleon Hash**: Fixed demo parameters, not production-ready

### Implementation Gaps

- `BlockCommit.check_redaction_policy()` exists but not fully wired to request flow
- Medical contract Solidity code has TODO placeholders (illustrative only)
- Multi-party secret sharing is stubbed, not fully implemented
- Policy enforcement could be more granular

### Not Included

- Production cryptographic security
- Real EVM bytecode execution
- Actual network layer (P2P)
- Persistent storage beyond simulation runs

## Contributing

### Development Workflow

1. Keep changes minimal and focused
2. Run tests before committing: `pytest tests/`
3. Update docs if changing public interfaces
4. Follow existing code patterns
5. Test in both normal and testing modes

### Code Organization

- Keep simulation logic in `Models/Bitcoin/`
- Cryptographic primitives in `CH/` and `ZK/`
- Use case implementations in `medical/`
- Demos in `demo/`
- Tests in `tests/`

## References

### Papers Implemented

1. **Ateniese et al.** - "Redactable Blockchain – or – Rewriting History in Bitcoin and Friends" (2017)
   - Chameleon hash redaction foundation
   - Bitcoin-like blockchain model
   - Core redaction mechanism

2. **Avitabile et al.** - "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains"
   - Smart contract integration
   - Zero-knowledge proofs for redaction
   - Proof-of-consistency
   - Medical use case

### Related Work

- Deuber et al. "Redactable blockchain in the permissionless setting" (2019)
- Puddu et al. "μchain: How to Forget without Hard Forks" (2017)
- Botta et al. "Towards Data Redaction in Bitcoin" (2022)

---

**For questions or issues, check `todo.md` for known gaps and planned improvements.**
