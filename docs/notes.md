# Notes

## Why This Codebase Benchmarks Ateniese’s Redactable Blockchain

Purpose

- Provide a concise rationale, with concrete code references, showing how this repo implements and benchmarks the core ideas from “Redactable Blockchain — or — Rewriting History in Bitcoin and Friends” (Ateniese et al.).

Core Mechanism (Chameleon-Hash–Based Redaction)

- Implements a chameleon hash primitive with trapdoor forging (centralized and multi‑party variants): `CH/ChameleonHash.py`.
- Block ids are computed via a chameleon hash; after editing a historical block, the trapdoor is used to forge a new randomness `r` that preserves the hash chain, i.e., “rewrite history” without breaking validity (paper’s key idea).
- In code: `Models/Bitcoin/BlockCommit.py` calls `forge(...)` and `chameleonHash(...)` to recompute `block.id` when transactions are deleted/modified.

Where It Lives in the Code

- Chameleon hash and forging: `CH/ChameleonHash.py` (plus `CH/SecretSharing.py` hooks for split/trapdoor sharing).
- Redaction operations: `Models/Bitcoin/BlockCommit.py` → `delete_tx(...)` and `redact_tx(...)` recompute `m1/m2`, forge `r2`, and set the new `block.id`.
- Redaction event driver: `BlockCommit.generate_redaction_event(...)` repeatedly applies redactions for benchmarking.
- Bitcoin-like backbone (per the paper’s model): `Models/Bitcoin/*` (mining, propagation, longest-chain resolution) with `Consensus`, `Node`, `BlockCommit`, `Block`.

Redaction Workflow (Matches the Paper’s Model)

- Choose a historical block/transaction; update or delete it.
- Compute the new message digest (transactions + previous hash) and use the trapdoor to forge `r2` such that `CH(new_msg, r2) = CH(old_msg, r1)` semantics hold.
- Update the block’s `id` and propagate consistent state across nodes; chain remains valid without global recomputation.
- In code paths: `delete_tx(...)` / `redact_tx(...)` and subsequent peer updates in `BlockCommit.py`.

Bitcoin-Like Simulation for Benchmarks

- Event‑driven network and mining simulate realistic conditions to measure impact: `Scheduler.py`, `Models/Network.py`, `Models/Bitcoin/Consensus.py`.
- Configurable parameters for reproducible experiments: `InputsConfig.py` (nodes, miners ratio, block interval/size, tx rate, redaction runs).
- Redaction frequency and mode toggles (`hasRedact`, `hasMulti`) enable controlled experimental scenarios.

Multi‑Party/Threshold Variants (Paper Discussion)

- Hooks for multi‑party chameleon/trapdoor sharing: `CH/SecretSharing.py`, references in `BlockCommit.setupSecretSharing()` and multi‑party branches (`hasMulti`).
- Demonstrates collaborative/threshold flavor of redaction as considered in the literature.

Benchmarking Outputs and Metrics

- Measures elapsed redaction time per operation and miner reward adjustments (cost/impact proxy): timing and reward logic in `BlockCommit.py`.
- Global statistics and export for analysis: `Statistics.py` (Excel/CSV via `openpyxl`/`xlsxwriter`).
- Transaction/block counters, chain lengths, and per‑run summaries are produced for performance comparisons.

Validation and Tests

- Test suite exercises redact/modify paths and coherence of the chain: `tests/` (e.g., minimal redaction tests and integration flows) with all tests passing.
- Ensures correctness properties needed for trustworthy benchmarking (no broken links in the hash chain after redaction).

Extended Components (Beyond Ateniese Baseline)

- Smart contracts, SNARK‑like proofs, proof‑of‑consistency, and IPFS flows are layered on top for newer research directions (e.g., Avitabile et al.).
- These do not replace the Ateniese baseline; the core chameleon‑hash redaction and Bitcoin‑style simulation remain the benchmark foundation.

How to Exercise as a Benchmark

- Configure experiment knobs in `InputsConfig.py` (e.g., `NUM_NODES`, `Binterval`, `Tn`, `hasRedact`, `redactRuns`, `hasMulti`).
- Run the simulator: `python Main.py` (generates blocks, transactions, and redactions; emits timing and stats).
- Collect results from console and `Statistics.py` outputs for cross‑run comparison.

Bottom Line

- This repository operationalizes the Ateniese redactable blockchain by embedding chameleon‑hash‑based block rewriting within a Bitcoin‑like simulator, exposing parameters and metrics to evaluate performance and behavior—i.e., a practical benchmark implementation of the paper’s central mechanism.

## Why There Are “Bitcoin Smart Contracts” And For Which Paper

Why They Exist

- To evaluate redactable blockchains in a smart‑contract–enabled setting where application logic, governance, and audit policies live on-chain. This extends the Ateniese benchmark to scenarios where contract state must remain consistent under redaction and redactions are governed by rules/roles.

Which Paper

- Implemented to support the proof‑of‑concept for: “Data Redaction in Smart‑Contract‑Enabled Permissioned Blockchains” (G. Avitabile, V. Botta, D. Friolo, I. Visconti). The repository’s README and demo (medical use case) explicitly target this paper.

How It’s Implemented Here (Simulated Contracts Over a Bitcoin‑Like Chain)

- Contract model and execution:
  - `Models/SmartContract.py`: Defines `SmartContract`, `ContractCall`, `ContractExecutionEngine`, `PermissionManager`, and `RedactionPolicy`.
  - `Models/Bitcoin/BlockCommit.py`: Integrates contract deploy/call handling during block processing.
  - `Main.py`: When smart contracts are enabled, deploys example contracts (audit/privacy) at startup for experiments.
- Domain logic and redaction orchestration:
  - `Enhanced/MedicalRedactionEngine.py`: Medical data contract state, redaction requests, approvals, and execution paths; links with SNARK‑like proofs and consistency checks.
  - `demo_medchain.py`: End‑to‑end flows (dataset creation, store/query, GDPR erasure, anonymization) demonstrating policy‑governed redactions.
- Configuration switches:
  - `InputsConfig.py`: `hasSmartContracts`, `hasPermissions`, `REDACTION_POLICIES`, and transaction mix including `CONTRACT_DEPLOY` / `CONTRACT_CALL` / `REDACTION_REQUEST` for scenario tuning.

Important Nuance

- Bitcoin itself does not natively provide this general smart‑contract model. Here, a Bitcoin‑like simulator is augmented with a lightweight contract layer to benchmark redactable‑blockchain behavior in a “smart‑contract‑enabled permissioned” environment as required by the Avitabile paper.

## Why This Repo Benchmarks the Avitabile Paper

- Covers the full smart‑contract redactable setting
  - Implements a permissioned, smart‑contract–enabled chain where data can be redacted without breaking consistency, matching “Data Redaction in Smart‑Contract‑Enabled Permissioned Blockchains”.

- Smart‑contract governance of redaction
  - Contracts, calls, deployment, and policy objects govern who can redact and when.
  - Files: `Models/SmartContract.py` (SmartContract, ContractCall, ContractExecutionEngine, PermissionManager, RedactionPolicy),
    `Models/Bitcoin/BlockCommit.py` (integration of deploy/call in block processing), `Main.py` (example contracts).

- Zero‑knowledge proofs (SNARK‑like) integration
  - `ZK/SNARKs.py` defines proof structure, circuit scaffolding, replay protection, and verification; used to validate redactions without leaking sensitive data.
  - Consumed by `Enhanced/MedicalRedactionEngine.py` and exercised in `demo_medchain.py`.

- Proof‑of‑consistency after redaction
  - `ZK/ProofOfConsistency.py` checks block integrity, Merkle paths, hash chain, transaction ordering, and smart‑contract state transitions post‑redaction.
  - Demo verifies both SNARK and consistency proofs in redaction flows.

- Permissioned RBAC and approvals
  - Role/permission model and quorum approvals simulate permissioned governance.
  - Files: `Models/SmartContract.PermissionManager`, `InputsConfig.py` (`hasPermissions`, `NODE_ROLES`, `minRedactionApprovals`, `REDACTION_POLICIES`).

- Medical use case and off‑chain linkage
  - `Enhanced/MedicalRedactionEngine.py` models medical records, consent, and redaction operations under policy.
  - `IPFS/MedicalDataIPFS.py` simulates censored data storage and linkage to on‑chain state.

- Configurable, measurable experiments
  - `InputsConfig.py` tunes nodes, block/tx rates, contract mix, redaction frequency; `Statistics.py` and timing in redaction paths provide metrics.

- Repeatable demo and tests
  - `demo_medchain.py` orchestrates dataset → contracts → proofs → consistency → redaction.
  - `tests/` ensure stability for benchmark runs (all passing).

- Built atop Ateniese baseline
  - Chameleon‑hash redactable chain forms the base, extended with contracts, proofs, and governance required by Avitabile’s setting.

## stuff to study

Overview

- Python simulation of a redactable, permissioned blockchain (Bitcoin‑like) with smart contracts,
  role‑based redaction governance, and a medical/IPFS demo.
- Core redaction uses chameleon hashes (Ateniese‑style). Smart contracts, SNARKs, proof‑of‑consistency,
  and IPFS are simulated to support the Avitabile paper use case.
- Entry points: Main.py (simulator) and multiple demos under demo/.

  Tech & Deps

- Python 3.9–3.11 (CI tests across versions).
- Deps: pandas, numpy, matplotlib, seaborn, requests, cryptography, pytest, openpyxl, xlsxwriter, typing-
  extensions.
- No real EVM/SNARK/IPFS libraries; these are modeled in Python for pedagogy/testing.

  How To Run

- Install: pip install -r requirements.txt
- Simulator: python Main.py
  - Quick config preview: TESTING_MODE=1 DRY_RUN=1 python Main.py
  - Fast mode: TESTING_MODE=1 python Main.py
- Demos:
  - Full MedChain: python -m demo.medchain_demo
  - Components: python ZK/SNARKs.py, python ZK/ProofOfConsistency.py, python -m
  demo.redactable_blockchain_demo, python -m demo.avitabile_*, python -m demo.medical_redaction_demo,
  python -m demo.ipfs_demo
- Tests: pytest -q tests (CI also generates coverage badge to badges/coverage.svg)

  Configuration

- InputsConfig.py: central config. Toggle testing mode via InputsConfig.initialize(testing_mode=True) or
  env var TESTING_MODE=1.
- Key toggles: hasRedact, hasSmartContracts, hasPermissions, minRedactionApprovals, REDACTION_POLICIES,
  transaction mix, network size.

  Core Structure

- Simulation
  - Main.py: drives runs; deploys example contracts; assigns roles; runs event loop; prints stats;
  writes Excel via Statistics.
  - Event.py + Scheduler.py: event queue + block creation/propagation.
  - Models/Bitcoin/*: concrete Bitcoin‑like mining/propagation, redaction workflow, longest‑chain.
  - Models/Transaction.py: transaction model + generators (TRANSFER, CONTRACT_CALL, CONTRACT_DEPLOY,
  REDACTION_REQUEST).
  - Models/Block.py: block structure incl. contract lists, redaction metadata, redaction history.
  - Models/Bitcoin/BlockCommit.py: the heart of block processing and redaction:
    - Computes block ids via chameleon hash.
    - Executes redactions by recomputing r with trapdoor: forge(...) + chameleonHash(...).
    - Simulates contract deploy/call handling and redaction voting/approval.
- Redaction primitives
  - CH/ChameleonHash.py, CH/SecretSharing.py: trapdoor hash + (simulated) secret sharing; uses fixed
  demo parameters and keys.
- Smart contracts (simulated)
  - Models/SmartContract.py: SmartContract, ContractCall, ContractExecutionEngine (gas calc + logs),
  PermissionManager, RedactionPolicy.
- ZK & Consistency (simulated)
  - ZK/SNARKs.py: defines proof objects, a “circuit” scaffold, commitment/nullifier, and heuristic
  verifier; demo/test harness included.
  - ZK/ProofOfConsistency.py: proof object + generators and verifiers for block/hash chain/Merkle/
  contract‑state/ordering.
- Medical + IPFS (simulated)
  - medical/MedicalRedactionEngine.py: medical contract wrapper, redaction requests → SNARK creation →
  approvals → execution; audit trail.
  - medical/MedicalDataIPFS.py: in‑memory “IPFS” client persisting to /tmp/fake_ipfs; dataset
  generator; patient mappings; redaction with versioning and integrity checks.

  Redaction Flow

- Block redaction:
  - Pick block+tx → modify/delete → recompute m2 (tx list + prev) → forge new r2 with trapdoor so
  CH(new_msg, r2) = CH(old_msg, r1) → update block id → propagate.
- Governance:
  - InputsConfig assigns node roles (ADMIN, REGULATOR, MINER, USER, OBSERVER).
  - Redaction request txs → request created by authorized roles → voting simulated among ADMIN/
  REGULATOR → on quorum, apply redaction and record approvals/history.

  Demos

- demo/redactable_blockchain_demo.py: minimal chameleon‑hash redaction demo.
- demo/avitabile_*: themed demos for redaction, consistency proofs, and a censored‑IPFS pipeline.
- demo/medchain_demo.py: orchestrates dataset → storage → access → GDPR erasure → proofs → audit →
  advanced redaction.

  Tests

- tests/ contains unit/integration/performance tests across:
  - Transactions, node/network basics, redact paths, smart contracts, permission manager.
  - ZK and consistency demo functions.
  - IPFS/medical redaction flows.
  - Avitabile demo harnesses.

  Notable Limitations/Gaps

- Simulations:
  - SNARKs, contract execution, and IPFS are proof‑of‑concept models; not real cryptographic/EVM/IPFS
  systems.
  - Chameleon hash secrets/params are hardcoded and suitable only for demonstration.
- Policy enforcement:
  - Models/Bitcoin/BlockCommit.py.check_redaction_policy(...) exists but isn’t wired into the redaction
  request flow. Quorum is driven by minRedactionApprovals without explicit per‑policy checks at request
  time.
- Medical contract code strings include TODO placeholders (non‑executed, illustrative).
- todo.md tracks broader tasks (censored pipeline completeness, policy checks E2E, more negative tests,
  demo CRUD surface, code cleanups).

How to use the real IPFS client

- Start a local IPFS node: ipfs daemon
- Copy .env.example to .env and set:
  - USE_REAL_IPFS=1
  - optionally IPFS_API_ADDR=/ip4/127.0.0.1/tcp/5001/http
- Create IPFSMedicalDataManager() without passing a client, or pass adapters.ipfs.get_ipfs_client()
yourself.
- Existing tests continue using the simulated client.
