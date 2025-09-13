# Developer Guide

This project simulates a redactable, permissioned blockchain with smart contracts, role-based governance, and a medical data use case that includes IPFS-backed storage and proof-of-concept zero-knowledge and consistency proofs.

## Structure Overview

- Core simulation
  - `Main.py`: Runs the blockchain simulation using `InputsConfig.py`.
  - `InputsConfig.py`: All model parameters, node/role setup, policies, and testing mode.
  - `Event.py`, `Scheduler.py`: Discrete-event engine (create/receive block events).
  - `Models/Block.py`: Block structure (transactions, chameleon-hash `r`, redaction metadata).
  - `Models/Transaction.py`: Transaction model and generators (TRANSFER, CONTRACT_CALL, CONTRACT_DEPLOY, REDACTION_REQUEST).
  - `Models/Bitcoin/BlockCommit.py`: Mining, propagation, chain updates, redaction execution and voting.
  - `Models/Bitcoin/Node.py`: Nodes with hashrate, roles/permissions, smart-contract deployment, redaction request/vote.
  - `Statistics.py`: Aggregated metrics (blocks, stale, contracts, redactions).

- Smart contracts (simulated)
  - `Models/SmartContract.py`: In-memory contract model, execution engine (gas calc + logs), permission manager.

- Redaction primitives
  - `CH/ChameleonHash.py`, `CH/SecretSharing.py`: Chameleon hash primitives for forgery (change block data without breaking the chain).

- ZK and consistency proofs (proof-of-concept)
  - `ZK/SNARKs.py`: Demonstration SNARK-like interface (commitments, nullifiers, verification heuristics).
  - `ZK/ProofOfConsistency.py`: Proof-of-consistency generators and verifiers for blocks, Merkle trees, hash chain, and contract state.

- Medical use case + IPFS
  - `medical/MedicalRedactionEngine.py`: Contract-backed medical records, redaction approvals, SNARK + consistency integration.
  - `medical/MedicalDataIPFS.py`: Fake IPFS client, dataset generator, patient-data mapping, redaction with versioning.
  - `demos/medchain_demo.py`: End-to-end demo across dataset → blockchain → proofs → audits.

- Tests
  - `tests/`: Integration/performance and feature tests (SNARK, IPFS, redaction flow, consistency).

## Run Modes

- Standard simulation
  - Install deps: `pip install -r requirements.txt`
  - Run: `python Main.py`
  - Tuning: edit `InputsConfig.py` (e.g., `NUM_NODES`, `hasSmartContracts`, `hasPermissions`, `REDACTION_POLICIES`).

- Testing mode (faster, smaller)
  - In `InputsConfig.py`: call `InputsConfig.initialize(testing_mode=True)` (or toggle `TESTING_MODE=True`).
  - Effects: fewer nodes, faster block interval, higher tx rates; richer policy set and logs.

- MedChain demo (full stack)
  - Run: `python -m demos.medchain_demo`
  - Phases: dataset → store in contract → access control → GDPR delete → SNARK + consistency proofs → audit reports → advanced scenarios.

- Component demos
  - `python ZK/SNARKs.py`
  - `python ZK/ProofOfConsistency.py`
  - `python -m demos.medical_redaction_demo`
  - `python -m demos.ipfs_demo`
  - `python -m demos.redactable_blockchain_demo`
  - `python -m demos.avitabile_redaction_demo`
  - `python -m demos.avitabile_consistency_demo`

## Key Concepts

- Redaction via chameleon hashes: enables mutating block contents while preserving chain validity.
- Permissioned governance: admins/regulators approve redactions (DELETE, ANONYMIZE, MODIFY) via quorum.
- Smart contracts and proofs are simulated for pedagogy — not production crypto or EVM.

## Tips

- For heavy runs, lower `NUM_NODES`, `simTime`, or switch to testing mode.
- To control tx mix, adjust `TRANSACTION_TYPE_DISTRIBUTION` in `InputsConfig.py`.
- To trace redaction workflow, watch logs from `BlockCommit.process_redaction_requests` and `Statistics.permission_results()`.

## Contributing

- Keep changes minimal and focused.
- Prefer small, testable patches.
- Update docs if changing public interfaces, configs, or workflows.

## Env Flags

- TESTING_MODE: Enables/disables testing mode without editing files.
  - Truthy values: `1`, `true`, `yes`, `on` (case-insensitive)
  - Falsy values: `0`, `false`, `no`, `off`
  - Examples:
    - `TESTING_MODE=1 python3 Main.py`  # small, fast sim
    - `TESTING_MODE=0 python3 Main.py`  # standard defaults

- DRY_RUN: Prints configuration summary and exits before running the simulation.
  - Combine with `TESTING_MODE` to preview config:
    - `TESTING_MODE=1 DRY_RUN=1 python3 Main.py`
    - `TESTING_MODE=0 DRY_RUN=1 python3 Main.py`
