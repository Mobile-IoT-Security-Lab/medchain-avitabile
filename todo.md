# Todos and Directives

## Professor and Boss Directives

We must implement the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" end‑to‑end. Starting from the Ateniese redactable blockchain benchmarks (<https://github.com/karimboubouh/Redactable_blockchain_benchmarks/tree/main/Redaction_Ateniese>), we add smart‑contract support and build a POC with a medical use case. First, demonstrate redactable blockchains with contracts, zero‑knowledge proofs (SNARKs), and proof‑of‑consistency. Then generate a synthetic medical dataset, build a censored version, upload only the censored version to IPFS (linked to the original). Provide a demo with CRUD (add/read/update/delete) and GDPR Right‑to‑be‑Forgotten via the Avitabile implementation.

## Real Implementation

1. [x] <!-- ### Core Architecture Changes --> Create `adapters/` directory structure
2. [x] Implement `adapters/config.py` with environment variable handling
3. [x] Add configuration flags: `USE_REAL_EVM`, `USE_REAL_SNARK`, `USE_REAL_IPFS` (default to simulation)
4. [x] Create `.env` template file with all required environment variables
5. [x] Update requirements: add `web3>=6`, `ipfshttpclient==0.8.0a2`, `cryptography`, `python-dotenv`
6. [x] IPFS Client Setup <!-- IPFS Implementation (Phase 1 - Lowest Friction) -->
7. [x] Set up local Kubo node (`ipfs daemon`) or configure pinning service
8. [x] Install and configure `ipfshttpclient` dependency
9. [x] Implement `adapters/ipfs.py` with `RealIPFSClient` class
10. [x] Mirror all `FakeIPFSClient` methods: `add`, `get`, `pin`, `unpin`, `rm`, `ls`, `stat`
11. [x] Add IPFS configuration variables: `IPFS_API_URL`, `IPFS_GATEWAY_URL`
12. [x] <!-- ### IPFS Encryption and Security --> Implement AES-GCM encryption for PHI before IPFS upload
13. [x] Design off-chain key management system (KMS or wallet-encrypted blob)
14. [x] Store only IPFS CID + ciphertext hash on-chain
15. [x] Implement "redaction by erasure": key rotation + content unpinning
16. [x] Update `IPFSMedicalDataManager` to accept any client interface <!-- ### IPFS Integration -->
17. [x] Inject `RealIPFSClient` when `USE_REAL_IPFS=1`
18. [x] Maintain backward compatibility with `FakeIPFSClient` for tests

19. [x] <!-- ### Smart Contract Development --> Initialize Hardhat or Foundry project in `contracts/` directory
20. [x] Create `contracts/MedicalDataManager.sol` from pseudo-code in `MedicalDataContract._get_medical_contract_code()`
21. [x] Implement mappings for: patient records (IPFS hash + metadata), redaction requests/approvals, events
22. [x] Ensure no PHI stored on-chain, only content identifiers and commitments
23. [x] Add events for all major operations (data storage, redaction requests, approvals)

24. [x] <!-- ### SNARK Verifier Contract --> Create `contracts/RedactionVerifier.sol` (to be generated from snarkjs)
25. [x] Integrate verifier contract with `MedicalDataManager.sol`
26. [x] Require valid proofs on redaction requests via `verifyProof(...)`

27. [x] <!-- ### Contract Deployment and Tooling --> Set up compilation and deployment scripts
28. [x] Deploy contracts to devnet using Hardhat Node or Anvil
29. [x] Export ABI and deployed addresses to `artifacts/` directory
30. [x] Add environment variables: `WEB3_PROVIDER_URI`, `EVM_PRIVATE_KEY`, `EVM_CHAIN_ID`
31. [x] Add contract addresses: `MEDICAL_CONTRACT_ADDRESS`, `VERIFIER_CONTRACT_ADDRESS`

32. [x] <!-- ### Python EVM Integration --> Implement `adapters/evm.py` with `EVMClient` class using `web3.py`
33. [x] Add connection, deployment, and contract loading functionality
34. [x] Create wrappers for contract methods: `storeMedicalData`, `requestDataRedaction`, approvals (execution handled off‑chain/simulated)
35. [x] Implement event query functionality
36. [x] Update `medical/MedicalRedactionEngine.py` to use `EVMClient` instead of `Models/SmartContract.*`
37. [x] Refactor current implementation as "SimulatedBackend" behind config flag

38. [x] <!-- ### Circuit Development --> Install Node.js dependencies: Hardhat/Foundry, circom, snarkjs
39. [x] Implement `redaction.circom` circuit proving...
40. [x] ...H(original) computation
41. [x] ...H(redacted) computation
42. [x] ...Policy hash matching
43. [x] ...Optional Merkle membership proof
44. [x] Compile circuit with circom
45. [x] Run Groth16 trusted setup ceremony
46. [x] Export Solidity verifier: `snarkjs zkey export solidityverifier` → `contracts/RedactionVerifier.sol`
47. [ ] <!-- ### Off-chain Proof Generation --> Implement `adapters/snark.py` wrapping snarkjs functionality
48. [ ] Add witness building functionality
49. [ ] Implement proof and public signal generation
50. [ ] Format calldata for Solidity `verifyProof(...)` method
51. [ ] Replace `ZK/SNARKs.py` usage in `MyRedactionEngine` with new adapter
52. [ ] Keep existing class as mock fallback for testing

53. [x] <!-- ### On-chain Verification Integration --> Update `MedicalDataManager.sol` to require proof verification before redaction operations
54. [x] Implement proper error handling for invalid proofs
55. [ ] Add events for successful/failed proof verifications

56. [ ] <!-- ### Unit Tests (Simulation Mode) --> Ensure all existing unit tests continue to pass with simulation backends
57. [ ] Add tests for new adapter interfaces
58. [ ] Test configuration switching between real and simulated backends

59. [ ] <!-- ### Integration Tests --> Create `pytest -m integration` test suite
60. [ ] Add devnet startup/teardown functionality
61. [ ] Implement contract deployment in test setup
62. [ ] Create E2E test flow: IPFS upload → redaction request → on-chain verification → pointer update
63. [ ] Add environment validation (skip tests if required services unavailable)

64. [ ] <!-- ### Cross-Component Testing --> Test IPFS ↔ EVM integration (CID storage and retrieval)
65. [ ] Test SNARK ↔ EVM integration (proof generation and verification)
66. [ ] Test full redaction pipeline across all three components

67. [ ] <!-- ### Documentation Updates --> Update README with real backend setup instructions
68. [ ] Document environment variable configuration
69. [ ] Add deployment and development setup guides
70. [ ] Document adapter pattern and fallback mechanisms
71. [ ] Add troubleshooting section for common setup issues

72. [ ] <!-- ### Code Quality --> Refactor existing simulation code to implement common interfaces
73. [ ] Add proper error handling and logging throughout adapters
74. [ ] Implement connection health checks for external services
75. [ ] Add configuration validation and helpful error messages

76. [ ] <!-- ### Production Readiness --> Add connection pooling and retry logic for external services
77. [ ] Implement proper secret management for private keys
78. [ ] Add monitoring and alerting for adapter health
79. [ ] Consider gas optimization for EVM operations
80. [ ] Plan for IPFS content pinning strategy in production

### Important Notes

- Public EVM cannot delete transaction history/logs; redaction operates at application/data layer only
- Protocol-level redaction requires permissioned blockchain with chameleon-hash support
- Keep Python simulation as reliable fallback for development and testing
- Implement suggested order: IPFS → EVM → SNARKs for incremental progress

## Todos (Aligned with Directives)

- [ ] Add real backends behind clean interfaces.
- [ ] Progressively swap simulated pieces for production tools.

- Paper implementation
  - [x] Integrate redactable blockchain with smart contracts (baseline in repo)
  - [x] Implement SNARKs for redaction proofs
  - [x] Implement proof‑of‑consistency for redactions
  - [ ] Orchestrate redaction via smart contracts (state + policy checks end‑to‑end)

- Medical dataset and censorship pipeline
  - [x] Generate synthetic medical dataset (`MedicalDatasetGenerator`)
  - [ ] Build censored dataset (policy‑based PII removal/anonymization)
  - [ ] Upload only the censored dataset to IPFS
  - [ ] Persist original dataset entries on the simulated/benchmark permissionless blockchain with smart contracts
  - [ ] Link original (on‑chain) and censored (IPFS) datasets by IDs (e.g., `dataset_id`/`record_id` ↔ `ipfs_hash`) maintained in contract state
  - [ ] Enforce integrity links (hashes/commitments) between original and censored artifacts

- Demo and CRUD interface
  - [ ] Expose explicit CRUD operations (add/read/update/delete) in the demo
  - [x] Support Right to be Forgotten on‑chain (redaction request, approvals, chameleon‑hash update)
  - [x] Support IPFS‑side redaction (re‑upload redacted version, rotate hash)
  - [ ] Show SNARK proof generation/verification and consistency verification in demo steps
  - [ ] Display and verify ID mapping (on‑chain `dataset_id`/`record_id` ↔ censored `ipfs_hash`) during demo flows
  - [ ] Enforce role‑based access (ADMIN/REGULATOR/PHYSICIAN/RESEARCHER) on CRUD/redactions

- Tests and validation
  - [ ] Censored pipeline tests (policy correctness, linkage integrity)
  - [ ] SNARK verifier negatives (replay/nullifier reuse, invalid challenge, timestamp window)
  - [ ] Consistency proof negatives (Merkle mismatch, broken hash chain, ordering changes)
  - [ ] IPFS integrity/redaction tests (pre/post equivalence minus censored fields)
  - [ ] Demo E2E: CRUD + Right to be Forgotten

- Documentation
  - [ ] Update README: censored‑IPFS model, on‑chain linkage, audit trail
  - [ ] Add compliance mapping to GDPR Art. 17 and HIPAA de‑identification
  - [ ] Document ID‑based linkage: original on simulated permissionless smart‑contract blockchain; censored data on IPFS only
  - [ ] Document architecture: base abstract modules vs. Bitcoin concrete implementations
  - [ ] Add an architecture diagram showing data flow: original on‑chain ↔ censored IPFS

- Code quality and fixes
  - [ ] Fix stray `self.executed_redactions.a` in `medical/MedicalRedactionEngine.py`
  - [ ] Clarify `ContractExecutionEngine.execute_call` (optional state mutation or remove unused local)
  - [ ] Clean TODOs in `MedicalDataContract` placeholders to match demo behavior
  - [ ] Several TODOs and proof‑of‑concept simplifications remain (e.g., simulated execution engine; TODOs in medical contract code comments)
  - [ ] Make `Models/Consensus.py` and `Models/BlockCommit.py` explicitly abstract (docstrings/NotImplementedError) (concrete logic lives under `Models/Bitcoin/`)
  - [ ] Ensure entrypoints use `Models/Bitcoin/*` implementations (no accidental base usage)
  - [ ] Add smoke tests that import and exercise Bitcoin consensus/block commit explicitly

- Performance/observability
  - [ ] Basic profiling for proof generation, redaction voting, block processing
  - [ ] Toggleable detailed logging via config for demo/tests
