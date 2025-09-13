# MedChain Project

[![Tests](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Mobile-IoT-Security-Lab/medchain-avitabile/actions/workflows/tests.yml) ![Coverage](badges/coverage.svg)

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

### Complete Demo System (`demos/medchain_demo.py`)

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

## My Implementation Features

- **Smart Contract Support** (Models/SmartContract.py): Full lifecycle management with deployment, execution, and state management for audit, privacy compliance, and general-purpose contracts
- **Role-Based Access Control**: Five permission levels from OBSERVER (read-only) to ADMIN (full system control) with specific capabilities for each role
- **Advanced Redaction Types**: DELETE (complete removal), MODIFY (selective editing), and ANONYMIZE (privacy protection) with multi-signature approval workflows
- **Privacy & Compliance**: Built-in GDPR, HIPAA, and SOX compliance with configurable data retention policies and automated privacy level enforcement
- **Transaction Distribution** (Models/Transaction.py): Optimized mix of transfers (80%), contract calls (10%), deployments (5%), and redaction requests (5%)
- **Test suite**.
- **Improved scripts**: Models/Transaction.py, Models/Bitcoin/Node.py, Models/Block.py, Models/Bitcoin/BlockCommit.py, InputsConfig.py, Main.py, Statistics.py

## Getting Started

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
python -m demos.medchain_demo

# Run individual component demos
python ZK/SNARKs.py
python ZK/ProofOfConsistency.py
python -m demos.medical_redaction_demo
python -m demos.ipfs_demo
python -m demos.redactable_blockchain_demo
python -m demos.avitabile_redaction_demo
python -m demos.avitabile_consistency_demo
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
