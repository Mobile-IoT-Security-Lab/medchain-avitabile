# todos and directives

## professor and boss directives

we have to implement the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" completely. starting from the Ateniese implementation of redactable blockchains at (<https://github.com/karimboubouh/Redactable_blockchain_benchmarks/tree/main/Redaction_Ateniese>) benchmarks, we have to add the support for smart contracts and implement a proof-of-concept for the paper using a medical use case. in particular, first we have to demonstrate the capabilities of redactable blockchains with smart contracts, through a simple smart contract, zero-knowledge proofs, snarks, and a proof-of-consistency. then we have to generate a fake dataset of medical data of patients, and don't upload it to IPFS, but create a censored version of the dataset, and upload only the censored version to IPFS, that will link to the original dataset. now that we have the original dataset on a permissionless blockchain and the censored version on the ipfs, we have to create a demo script that allows users to query (add, read, update, delete) the dataset, and that allows patients to exercise their right to be forgotten, by redacting the blockchain record using the avitabile "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" implementation.

## todos (aligned with directives)

- [ ] add real backends behind clean interfaces,
- [ ] progressively swap the simulated pieces for production tools.

- Paper implementation
  - [x] Integrate redactable blockchain with smart contracts (baseline in repo)
  - [x] Implement SNARKs for redaction proofs
  - [x] Implement proof-of-consistency for redactions
  - [ ] Orchestrate redaction via smart contracts (state + policy checks end-to-end)

- Medical dataset and censorship pipeline
  - [x] Generate synthetic medical dataset (`MedicalDatasetGenerator`)
  - [ ] Build censored dataset (policy-based PII removal/anonymization)
  - [ ] Upload only the censored dataset to IPFS
  - [ ] Persist original dataset entries on the simulated/benchmark permissionless blockchain with smart contracts
  - [ ] Link original (on-chain) and censored (IPFS) datasets by IDs (e.g., `dataset_id`/`record_id` ↔ `ipfs_hash`) maintained in contract state
  - [ ] Enforce integrity links (hashes/commitments) between original and censored artifacts

- Demo and CRUD interface
  - [ ] Expose explicit CRUD operations (add/read/update/delete) in the demo
  - [x] Support Right to be Forgotten on-chain (redaction request, approvals, chameleon-hash update)
  - [x] Support IPFS-side redaction (re-upload redacted version, rotate hash)
  - [ ] Show SNARK proof generation/verification and consistency verification in demo steps
  - [ ] Display and verify ID mapping (on-chain `dataset_id`/`record_id` ↔ censored `ipfs_hash`) during demo flows
  - [ ] Enforce role-based access (ADMIN/REGULATOR/PHYSICIAN/RESEARCHER) on CRUD/redactions

- Tests and validation
  - [ ] Censored pipeline tests (policy correctness, linkage integrity)
  - [ ] SNARK verifier negatives (replay/nullifier reuse, invalid challenge, timestamp window)
  - [ ] Consistency proof negatives (Merkle mismatch, broken hash chain, ordering changes)
  - [ ] IPFS integrity/redaction tests (pre/post equivalence minus censored fields)
  - [ ] Demo E2E: CRUD + Right to be Forgotten

- Documentation
  - [ ] Update README: censored-IPFS model, on-chain original linkage, audit trail
  - [ ] Add compliance mapping to GDPR Art. 17 and HIPAA de-identification
  - [ ] Document explicit ID-based linkage: original on simulated permissionless smart-contract blockchain; censored data on IPFS only
  - [ ] Document architecture: base abstract modules vs. Bitcoin concrete implementations
  - [ ] Add an architecture diagram showing data flow: original on-chain ↔ censored IPFS

- Code quality and fixes
  - [ ] Fix stray `self.executed_redactions.a` in `medical/MedicalRedactionEngine.py`
  - [ ] Clarify `ContractExecutionEngine.execute_call` (optional state mutation or remove unused local)
  - [ ] Clean TODOs in `MedicalDataContract` placeholders to match demo behavior
  - [ ] Some TODOs and “proof-of-concept” simplifications exist (e.g., `ContractExecutionEngine.execute_call` logic is simulated; several TODOs in medical contract code comments).
  - [ ] Make `Models/Consensus.py` and `Models/BlockCommit.py` explicitly abstract (docstrings/NotImplementedError) (concrete logic lives under `Models/Bitcoin/`).
  - [ ] Ensure all entrypoints/reference code use `Models/Bitcoin/*` implementations (no accidental base usage)
  - [ ] Add smoke tests that import and exercise Bitcoin consensus/block commit explicitly

- Performance/observability
  - [ ] Basic profiling for proof generation, redaction voting, block processing
  - [ ] Toggleable detailed logging via config for demo/tests
