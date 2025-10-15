# MedChain: Redactable Blockchain with Smart Contracts

[![Tests](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/tests.yml) ![Python Coverage](badges/python-coverage.svg) [![Contracts](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/contracts.yml/badge.svg?branch=main)](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/contracts.yml) ![Solidity Coverage](badges/solidity-coverage.svg)

A Python blockchain simulator implementing **chameleon hash-based redaction** with smart contract governance, zero-knowledge proofs, and medical data GDPR compliance.

**Research Papers:**

- **Ateniese et al.** (2017) - Chameleon hash-based blockchain redaction  
- **Avitabile et al.** - Smart contract governance with zero-knowledge proofs

**Key Innovation:** Rewrite blockchain history without breaking the chain using cryptographic trapdoors.

**Research Papers:**

- **Ateniese et al.** (2017) - Chameleon hash-based blockchain redaction  
- **Avitabile et al.** - Smart contract governance with zero-knowledge proofs

## Quick Start

\`\`\`bash
git clone <https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile.git>
cd medchain-avitabile
pip install -r requirements.txt
python Main.py
\`\`\`

## Core Concepts

### Chameleon Hash Redaction

\`\`\`
CH(m, r) = g^m · PK^r mod p
\`\`\`

1. Select historical block for modification
2. Compute new message (updated transactions + previous hash)
3. Forge new randomness: \`r2 = forge(SK, m1, r1, m2)\`
4. Result: \`CH(m1, r1) = CH(m2, r2)\` - same hash, different content
5. Chain remains valid

### Features

| Feature | Description |
|---------|-------------|
| **Redaction Types** | DELETE, MODIFY, ANONYMIZE |
| **Smart Contracts** | Governance, audit, privacy compliance |
| **ZK Proofs** | SNARKs for private verification |
| **IPFS Integration** | Distributed storage with AES-GCM encryption |
| **Medical Use Case** | GDPR Article 17 compliance |
| **Roles** | ADMIN, REGULATOR, MINER, USER, OBSERVER |

## Usage

### Basic Simulation

\`\`\`bash
python Main.py                    # Standard mode
TESTING_MODE=1 python Main.py    # Fast mode
DRY_RUN=1 python Main.py         # Preview config
\`\`\`

### Demos

\`\`\`bash
python -m demo.medchain_demo                 # Full workflow
python -m demo.medical_redaction_demo        # Medical redaction
python -m demo.ipfs_demo                     # IPFS integration
python ZK/SNARKs.py                          # SNARK proofs
python ZK/ProofOfConsistency.py              # Consistency verification
\`\`\`

### Configuration

Edit \`InputsConfig.py\`:

\`\`\`python
Nodes = 20                       # Number of nodes
Binterval = 10                   # Block interval (seconds)
Tn = 5                          # Transactions per second
hasRedact = True
minRedactionApprovals = 2
hasSmartContracts = True
hasPermissions = True
\`\`\`

### Environment Variables

\`\`\`bash
TESTING_MODE=1              # Fast mode
USE_REAL_IPFS=1            # Real IPFS daemon
USE_REAL_EVM=1             # Real blockchain  
USE_REAL_SNARK=1           # Real SNARKs
IPFS_ENC_KEY=KEY_HERE      # AES-256 encryption key (base64)
\`\`\`

## Medical Use Case

### GDPR Right to be Forgotten

\`\`\`python
engine = MedicalRedactionEngine()
record_id = engine.store_patient_data(patient_data)

request_id = engine.request_redaction(
    record_id=record_id,
    redaction_type="DELETE",
    reason="GDPR Article 17"
)

engine.approve_redaction(request_id, approver="REGULATOR")
engine.approve_redaction(request_id, approver="ADMIN")

proof = engine.execute_redaction(request_id)
assert engine.verify_consistency(proof)
\`\`\`

## Project Structure

\`\`\`
medchain-avitabile/
├── Main.py                          # Simulator entry point
├── InputsConfig.py                  # Configuration
├── Models/
│   ├── Block.py                    # Block with chameleon hash
│   ├── Transaction.py              # Transaction types
│   ├── SmartContract.py            # Contract execution
│   └── Bitcoin/BlockCommit.py      # Mining + redaction
├── CH/ChameleonHash.py             # Trapdoor functions
├── ZK/
│   ├── SNARKs.py                   # Zero-knowledge proofs
│   └── ProofOfConsistency.py       # Integrity verification
├── medical/
│   ├── MedicalRedactionEngine.py   # GDPR compliance
│   └── MedicalDataIPFS.py          # Distributed storage
├── demo/                           # Demo scripts
└── tests/                          # Test suite
\`\`\`

## Testing

\`\`\`bash
pytest tests/                            # All tests
pytest -m "not slow"                    # Fast tests only
pytest tests/test_consistency_system.py  # Specific test
pytest --cov=. --cov-report=html        # With coverage
\`\`\`

## Performance

| Metric | Value |
|--------|-------|
| Nodes | 20-1000 (configurable) |
| Block Time | 10-600 seconds |
| Tx Rate | 5-10 tx/s |
| Redaction Time | ~2 seconds (simulated) |
| Proof Generation | ~5 seconds (real SNARKs) |

## Limitations

**Research prototype with simulated components:**

- SNARKs: Proof-of-concept (unless \`USE_REAL_SNARK=1\`)
- Smart Contracts: In-memory simulation (unless \`USE_REAL_EVM=1\`)
- IPFS: Simulated client (unless \`USE_REAL_IPFS=1\`)
- Chameleon Hash: Fixed demo parameters
- Network: No real P2P layer

**Not production-ready.** For research and education only.

## References

1. **Ateniese et al.** (2017) - [Redactable Blockchain](https://ieeexplore.ieee.org/abstract/document/7961975/)
2. **Avitabile et al.** - Data Redaction in Smart-Contract-Enabled Permissioned Blockchains
3. **Deuber et al.** (2019) - [Permissionless Setting](https://ieeexplore.ieee.org/abstract/document/8835372)
4. **Puddu et al.** (2017) - [μchain](https://eprint.iacr.org/2017/106)
5. **Botta et al.** (2022) - [Towards Data Redaction](https://doi.org/10.1109/TNSM.2022.3214279)

## Contributing

1. Fork the repository
2. Create feature branch
3. Run tests (\`pytest tests/\`)
4. Commit changes
5. Open Pull Request

## License

Academic research project. See institution policies for usage rights.

## Acknowledgments

- University of Genoa - Decentralized Systems Course
- [BlockSim](https://github.com/maher243/BlockSim) - Blockchain simulator framework

---

**For implementation details, see \`todo.md\`**
