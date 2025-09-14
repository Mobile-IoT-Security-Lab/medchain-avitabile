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
  - `demo/medchain_demo.py`: End-to-end demo across dataset → blockchain → proofs → audits.

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
  - Run: `python -m demo.medchain_demo`
  - Phases: dataset → store in contract → access control → GDPR delete → SNARK + consistency proofs → audit reports → advanced scenarios.

- Component demos
  - `python ZK/SNARKs.py`
  - `python ZK/ProofOfConsistency.py`
  - `python -m demo.medical_redaction_demo`
  - `python -m demo.ipfs_demo`
  - `python -m demo.redactable_blockchain_demo`
  - `python -m demo.avitabile_redaction_demo`
  - `python -m demo.avitabile_consistency_demo`
  - `python -m demo.avitabile_censored_ipfs_pipeline`

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

- IPFS_ENC_KEY: Base64‑encoded AES key for dataset encryption (AES‑GCM)
  - Length: 16/24/32 bytes (AES‑128/192/256)
  - Used by `medical/MedicalDataIPFS.IPFSMedicalDataManager` when `encrypt=True`
  - Upload: stores envelope `{enc:"AES-GCM",nonce,ciphertext}`; plaintext never hits IPFS
  - Download: decrypts automatically; if key is missing, AES‑GCM content is unreadable
  - Generate dev key (example AES‑256):
    - `python - <<'PY'`
    - `import os, base64; print(base64.b64encode(os.urandom(32)).decode())`
    - `PY`

## Key Providers and Rotation

- EnvKeyProvider
  - Reads from `IPFS_ENC_KEY` (base64) and optional `IPFS_ENC_KEY_ID`.
  - Maintains an optional pool `IPFS_ENC_KEYS` (JSON mapping kid→base64) to keep historical keys.
  - Rotation: `EnvKeyProvider.rotate()` sets a new active key and appends it to the pool.

- FileKeyProvider
  - Stores AES keys encrypted with passphrase (scrypt + AES‑GCM) in a JSON keystore (`keystore.json`).
  - Structure: `{ v, wrap: "AES-GCM-SCRYPT", params, keys: [ {kid,salt,nonce,ciphertext,klen}... ], active }`.
  - Rotation appends a new wrapped key and marks it `active`. Legacy single‑key files are auto‑upgraded on first rotation.
  - Use with manager:
    - `prov = FileKeyProvider('keystore.json', passphrase='change-me')`
    - `mgr = IPFSMedicalDataIPFS.IPFSMedicalDataManager(client, key_provider=prov)`
  - One‑liners:
    - Create/rotate: `python - <<'PY'\nfrom medical.key_provider import FileKeyProvider; prov=FileKeyProvider('keystore.json','pass'); print(prov.rotate())\nPY`
  - CLI helper (within repo):
    - `python scripts/keystore_cli.py rotate --provider file --keystore keystore.json --passphrase 'change-me'`
    - `python scripts/keystore_cli.py list   --provider file --keystore keystore.json --passphrase 'change-me'`

- EnvKeyProvider helpers
  - Rotate with random key and print export lines: `python scripts/keystore_cli.py rotate --provider env --print-exports`
  - List known ids: `python scripts/keystore_cli.py list --provider env`

## Multi‑Key Decryption and Erasure

- Envelopes include `kid` so the manager can ask the provider to resolve historical keys when decrypting.
- After rotating to a new key, data encrypted with previous keys remains readable if the provider retains those keys.
- To enforce data erasure:
  - Rotate to a new key.
  - Unpin/remove old IPFS content.
  - Remove old key entries (FileKeyProvider: edit keystore; EnvKeyProvider: remove from `IPFS_ENC_KEYS`).
  - Without the old key, ciphertext becomes unusable.
