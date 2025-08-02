# MedChain Project

This is a project for the Decentralized Systems course at the University of Genoa. Originally forked from the Redactable Blockchain Benchmarks repository, this project adds the support for smart contracts in the Ateniese implementation to implement a proof-of-concept for the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains". In particular, the MedChain project uses a medical use case to demonstrate the capabilities of redactable blockchains with smart contracts, focusing on patient data management and privacy compliance.

## todos

- [x] finish README.md
- [ ] implement completely the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains"
  - [ ] implement SNARKs
  - [ ] implement the proof-of-consistency
- [ ] Add more tests
- [ ] Add more documentation
- [ ] Create a Fake Dataset of Medical Data of Patients
- [ ] Upload the Dataset to IPFS
- [ ] Create a Demo Script that:
  - [ ] Using a Blockchain that Links to the IPFS Hash of or ID the Dataset
  - [ ] Allows Users to Query the Dataset
  - [ ] Allow Patients Right to be Forgotten
  - [ ] Redact the Blockchain Record
  - [ ] Redact the IPFS Record
  ...

## Overview

The original benchmarks focused on the implementation and evaluation of 3 redactable blockchain systems:

- **Redaction_Ateniese**: Chameleon hash-based redaction with improved smart contract support
- **Redaction_Deuber**: Voting-based redaction approach
- **Redaction_Puddu**: Mutation-based redaction (μchain approach)

I have improved the **Redaction_Ateniese** implementation to support smart contracts, getting inspiration from the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains".

## Improved Redaction_Ateniese Features

- **Smart Contract Support** (Models/SmartContract.py): Full lifecycle management with deployment, execution, and state management for audit, privacy compliance, and general-purpose contracts
- **Role-Based Access Control**: Five permission levels from OBSERVER (read-only) to ADMIN (full system control) with specific capabilities for each role
- **Advanced Redaction Types**: DELETE (complete removal), MODIFY (selective editing), and ANONYMIZE (privacy protection) with multi-signature approval workflows
- **Privacy & Compliance**: Built-in GDPR, HIPAA, and SOX compliance with configurable data retention policies and automated privacy level enforcement
- **Transaction Distribution** (Models/Transaction.py): Optimized mix of transfers (80%), contract calls (10%), deployments (5%), and redaction requests (5%)
- **Test suite**.
- **Improved scripts**: Models/Transaction.py, Models/Bitcoin/Node.py, Models/Block.py, Models/Bitcoin/BlockCommit.py, InputsConfig.py, Main.py, Statistics.py

## Getting Started

```bash
# Clone the repository
git clone [repository-url]

# Install dependencies
pip install -r requirements.txt

# Run the implementation
python Main.py
```

## Experimental Framework

The simulations in this project are conducted using the [BlockSim simulator](https://github.com/maher243/BlockSim). BlockSim is an open-source simulator specifically designed for blockchain systems. It provides intuitive simulation constructs and allows for customization to support multiple blockchain design and deployment scenarios.

### Improved Framework Features (Redaction_Ateniese)

The improved implementation extends BlockSim with:

- **Smart Contract Execution Engine**: Simulated smart contract deployment and execution
- **Permission Management System**: Role-based access control simulation
- **Privacy Policy Enforcement**: Automated privacy compliance checking
- **Multi-Signature Governance**: Simulated approval workflows for redaction requests
- **Performance Monitoring**: Advanced metrics collection and analysis

## Configuration Examples

### Basic Configuration (All Implementations)

```python
# InputsConfig.py
Nodes = 20                    # Number of nodes
Tn = 5                       # Transactions per second
Binterval = 10               # Block interval in seconds
hasRedact = True             # Enable redaction
redactionProbability = 0.1   # 10% of blocks may be redacted
```

### Improved Configuration (Redaction_Ateniese)

```python
# EnhancedInputsConfig.py
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
