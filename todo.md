# Todos and Directives

## new directives after alignment meeting

1. [x] Prioritize the implementation of zero-knowledge proofs (ZK Proofs) for data redaction
a. [x] mark every file used for the above step one with something like (Bookmark1 for next meeting)
   - **COMPLETED**: See `docs/ZK_IMPLEMENTATION_SUMMARY.md` and `docs/ZK_PROOF_IMPLEMENTATION_PLAN.md`
   - Implemented `medical/circuit_mapper.py` for proper medical data → circuit input mapping
   - Implemented `medical/my_snark_manager.py` with real Groth16 proof generation
   - Added comprehensive test suite in `tests/test_circuit_mapper.py`
   - Real SNARK proofs now work end-to-end
   - No more TODO placeholders in SNARK flow
   - **Bookmark1 Files Added**:
     - `medical/MedicalRedactionEngine.py`
     - `ZK/SNARKs.py`
     - `ZK/ProofOfConsistency.py`
     - `adapters/snark.py`
     - `tests/test_snark_system.py`
     - `tests/test_consistency_system.py`
     - `tests/test_consistency_circuit_integration.py`
   - **Next Phase**: On-chain verification integration (Phase 2)
2. [x] actually implement the avitabile addings to ateniese paper (snark proofs, proof of consistency, zk proofs), not a simulation
a. [x] mark every file used for the above step two with something like (Bookmark2 for next meeting)
   - **COMPLETED**: Phase 2 on-chain verification implementation finished
   - SNARKs use real Groth16 proofs (no simulation)
   - Proof of consistency implemented in `ZK/ProofOfConsistency.py`
   - **COMPLETED (Phase 1)**: Wire consistency proofs into circuit public inputs
     - Implemented in `medical/circuit_mapper.py`: `prepare_circuit_inputs_with_consistency()`
     - Integrated in `medical/my_snark_manager.py`: `create_redaction_proof_with_consistency()`
     - Test coverage in `tests/test_consistency_circuit_integration.py`
   - **COMPLETED (Phase 2)**: On-chain verification of both SNARK and consistency proofs
     - Implemented `contracts/src/NullifierRegistry.sol` for replay prevention
     - Enhanced `contracts/src/MedicalDataManager.sol` with full proof verification
     - Updated `medical/backends.py` EVMBackend with Phase 2 support
     - Updated `medical/MedicalRedactionEngine.py` to wire all proofs together
     - Created `tests/test_phase2_onchain_verification.py` for E2E testing
     - Created `tests/test_nullifier_registry.py` for nullifier contract testing
     - Created `contracts/scripts/deploy_phase2.js` for deployment
     - **Bookmark2 Files Added/Updated**:
       - `contracts/src/NullifierRegistry.sol` (NEW)
       - `contracts/src/MedicalDataManager.sol` (UPDATED with Phase 2)
       - `medical/backends.py` (UPDATED with full proof submission)
       - `medical/MedicalRedactionEngine.py` (UPDATED with Phase 2 integration)
       - `adapters/evm.py` (UPDATED with Bookmark2)
       - `ZK/SNARKs.py` (UPDATED with Bookmark2)
       - `ZK/ProofOfConsistency.py` (UPDATED with Bookmark2)
       - `medical/circuit_mapper.py` (UPDATED with Bookmark2)
       - `tests/test_phase2_onchain_verification.py` (NEW)
       - `tests/test_nullifier_registry.py` (NEW)
       - `contracts/scripts/deploy_phase2.js` (NEW)
       - `docs/PHASE_2_ON_CHAIN_VERIFICATION_PLAN.md` (NEW)
   - **NO MORE SIMULATION**: All proofs are real, all verification is on-chain
3. [ ] deliverables

## Professor and Boss Directives

I must implement the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" end‑to‑end. Starting from the Ateniese redactable blockchain benchmarks (<https://github.com/karimboubouh/Redactable_blockchain_benchmarks/tree/main/Redaction_Ateniese>), I add smart‑contract support and build a POC with a medical use case. First, I demonstrate redactable blockchains with contracts, zero‑knowledge proofs (SNARKs), and proof‑of‑consistency. Then I generate a synthetic medical dataset, build a censored version, upload only the censored version to IPFS (linked to the original), and provide a demo with CRUD (add/read/update/delete) and GDPR Right‑to‑be‑Forgotten via the Avitabile implementation.

## Real Implementation

0. [x] core structure changes
1. [x] Create `adapters/` directory structure
2. [x] Implement `adapters/config.py` with environment variable handling
3. [x] Add configuration flags: `USE_REAL_EVM`, `USE_REAL_IPFS` (SNARKs always real)
4. [x] Create `.env` template file with all required environment variables
5. [x] Update requirements: add `web3>=6`, `ipfshttpclient==0.8.0a2`, `cryptography`, `python-dotenv`
6. [x] IPFS Implementation (Phase 1 - Lowest Friction)
7. [x] IPFS Client Setup
8. [x] Set up local Kubo node (`ipfs daemon`) or configure pinning service
9. [x] Install and configure `ipfshttpclient` dependency
10. [x] Implement `adapters/ipfs.py` with `RealIPFSClient` class
11. [x] Mirror all `FakeIPFSClient` methods: `add`, `get`, `pin`, `unpin`, `rm`, `ls`, `stat`
12. [x] Add IPFS configuration variables: `IPFS_API_URL`, `IPFS_GATEWAY_URL`
13. [x] IPFS Encryption and Security
14. [x] Implement AES-GCM encryption for PHI before IPFS upload
15. [x] Design off-chain key management system (KMS or wallet-encrypted blob)
16. [x] Store only IPFS CID + ciphertext hash on-chain
17. [x] Implement "redaction by erasure": key rotation + content unpinning
18. [x] IPFS Integration
19. [x] Update `IPFSMedicalDataManager` to accept any client interface
20. [x] Inject `RealIPFSClient` when `USE_REAL_IPFS=1`
21. [x] Maintain backward compatibility with `FakeIPFSClient` for tests
22. [x] Smart Contract Development
23. [x] Initialize Hardhat or Foundry project in `contracts/` directory
24. [x] Create `contracts/MedicalDataManager.sol` from pseudo-code in `MedicalDataContract._get_medical_contract_code()`
25. [x] Implement mappings for: patient records (IPFS hash + metadata), redaction requests/approvals, events
26. [x] Ensure no PHI stored on-chain, only content identifiers and commitments
27. [x] Add events for all major operations (data storage, redaction requests, approvals)
28. [x] SNARK Verifier Contract
29. [x] Create `contracts/RedactionVerifier.sol` (to be generated from snarkjs)
30. [x] Integrate verifier contract with `MedicalDataManager.sol`
31. [x] Require valid proofs on redaction requests via `verifyProof(...)`
32. [x] Contract Deployment and Tooling
33. [x] Set up compilation and deployment scripts
34. [x] Deploy contracts to devnet using Hardhat Node or Anvil
35. [x] Export ABI and deployed addresses to `artifacts/` directory
36. [x] Add environment variables: `WEB3_PROVIDER_URI`, `EVM_PRIVATE_KEY`, `EVM_CHAIN_ID`
37. [x] Add contract addresses: `MEDICAL_CONTRACT_ADDRESS`, `VERIFIER_CONTRACT_ADDRESS`
38. [x] Python EVM Integration
39. [x] Implement `adapters/evm.py` with `EVMClient` class using `web3.py`
40. [x] Add connection, deployment, and contract loading functionality
41. [x] Create wrappers for contract methods: `storeMedicalData`, `requestDataRedaction`, approvals (execution handled off‑chain/simulated)
42. [x] Implement event query functionality
43. [x] Update `medical/MedicalRedactionEngine.py` to use `EVMClient` instead of `Models/SmartContract.*`
44. [x] Refactor current implementation as "SimulatedBackend" behind config flag
45. [x] Circuit Development
46. [x] Install Node.js dependencies: Hardhat/Foundry, circom, snarkjs
47. [x] Implement `redaction.circom` circuit proving...
48. [x] ...H(original) computation
49. [x] ...H(redacted) computation
50. [x] ...Policy hash matching
51. [x] ...Optional Merkle membership proof
52. [x] Compile circuit with circom
53. [x] Run Groth16 trusted setup ceremony
54. [x] Export Solidity verifier: `snarkjs zkey export solidityverifier` → `contracts/RedactionVerifier.sol`
55. [x] Off-chain Proof Generation
56. [x] Implement `adapters/snark.py` wrapping snarkjs functionality
57. [x] Add witness building functionality
58. [x] Implement proof and public signal generation
59. [x] Format calldata for Solidity `verifyProof(...)` method
60. [x] Replace `ZK/SNARKs.py` usage in `MyRedactionEngine` with new adapter
61. [x] Keep existing class as mock fallback for testing
62. [x] On-chain Verification Integration
63. [x] Update `MedicalDataManager.sol` to require proof verification before redaction operations
64. [x] Implement proper error handling for invalid proofs
65. [x] Add events for successful/failed proof verifications
66. [x] Unit Tests (Simulation Mode)
67. [x] Ensure all existing unit tests continue to pass with simulation backends
68. [x] Add tests for new adapter interfaces
69. [x] Test configuration switching between real and simulated backends
70. [x] Integration Tests
71. [x] Create `pytest -m integration` test suite
72. [x] Add devnet startup/teardown functionality
73. [x] Implement contract deployment in test setup
74. [x] Create E2E test flow: IPFS upload → redaction request → on-chain verification → pointer update
75. [x] Add environment validation (skip tests if required services unavailable)
76. [x] Cross-Component Testing
77. [x] Test IPFS  EVM integration (CID storage and retrieval)
78. [x] Test SNARK  EVM integration (proof generation and verification)
79. [x] Test full redaction pipeline across all three components
80. [ ] Documentation Updates
81. [ ] Update README with real backend setup instructions
82. [ ] Document environment variable configuration
83. [ ] Add deployment and development setup guides
84. [ ] Document adapter pattern and fallback mechanisms
85. [ ] Add troubleshooting section for common setup issues
86. [ ] Code Quality
87. [ ] Refactor existing simulation code to implement common interfaces
88. [ ] Add proper error handling and logging throughout adapters
89. [ ] Implement connection health checks for external services
90. [ ] Add configuration validation and helpful error messages
91. [ ] Production Readiness
92. [ ] Add connection pooling and retry logic for external services
93. [ ] Implement proper secret management for private keys
94. [ ] Add monitoring and alerting for adapter health
95. [ ] Consider gas optimization for EVM operations
96. [ ] Plan for IPFS content pinning strategy in production
97. [ ] Todos (Aligned with Directives)
98. [ ] Add real backends behind clean interfaces.
99. [ ] Progressively swap simulated pieces for production tools.
100. [x] Paper implementation
101. [x] Integrate redactable blockchain with smart contracts (baseline in repo)
102. [x] Implement SNARKs for redaction proofs
103. [x] Implement proof‑of‑consistency for redactions
104. [ ] Orchestrate redaction via smart contracts (state + policy checks end‑to‑end)
105. [x] Medical dataset and censorship pipeline
106. [x] Generate synthetic medical dataset (`MedicalDatasetGenerator`)
107. [ ] Build censored dataset (policy‑based PII removal/anonymization)
108. [ ] Upload only the censored dataset to IPFS
109. [ ] Persist original dataset entries on the simulated/benchmark permissionless blockchain with smart contracts
110. [ ] Link original (on‑chain) and censored (IPFS) datasets by IDs (e.g., `dataset_id`/`record_id`  `ipfs_hash`) maintained in contract state
111. [ ] Enforce integrity links (hashes/commitments) between original and censored artifacts
112. [ ] Demo and CRUD interface
113. [ ] Expose explicit CRUD operations (add/read/update/delete) in the demo
114. [x] Support Right to be Forgotten on‑chain (redaction request, approvals, chameleon‑hash update)
115. [x] Support IPFS‑side redaction (re‑upload redacted version, rotate hash)
116. [ ] Show SNARK proof generation/verification and consistency verification in demo steps
117. [ ] Display and verify ID mapping (on‑chain `dataset_id`/`record_id`  censored `ipfs_hash`) during demo flows
118. [ ] Enforce role‑based access (ADMIN/REGULATOR/PHYSICIAN/RESEARCHER) on CRUD/redactions
119. [ ] Censored pipeline tests
120. [ ] Censored pipeline tests (policy correctness, linkage integrity)
121. [ ] SNARK verifier negatives (replay/nullifier reuse, invalid challenge, timestamp window)
122. [ ] Consistency proof negatives (Merkle mismatch, broken hash chain, ordering changes)
123. [ ] IPFS integrity/redaction tests (pre/post equivalence minus censored fields)
124. [ ] Demo E2E: CRUD + Right to be Forgotten
125. [ ] Documentation
126. [ ] Update README: censored‑IPFS model, on‑chain linkage, audit trail
127. [ ] Add compliance mapping to GDPR Art. 17 and HIPAA de‑identification
128. [ ] Document ID‑based linkage: original on simulated permissionless smart‑contract blockchain; censored data on IPFS only
129. [ ] Document architecture: base abstract modules vs. Bitcoin concrete implementations
130. [ ] Add an architecture diagram showing data flow: original on‑chain  censored IPFS
131. [ ] Code quality and fixes
132. [ ] Fix stray `self.executed_redactions.a` in `medical/MedicalRedactionEngine.py`
133. [ ] Clarify `ContractExecutionEngine.execute_call` (optional state mutation or remove unused local)
134. [ ] Clean TODOs in `MedicalDataContract` placeholders to match demo behavior
135. [ ] Several TODOs and proof‑of‑concept simplifications remain (e.g., simulated execution engine; TODOs in medical contract code comments)
136. [ ] Make `Models/Consensus.py` and `Models/BlockCommit.py` explicitly abstract (docstrings/NotImplementedError) (concrete logic lives under `Models/Bitcoin/`)
137. [ ] Ensure entrypoints use `Models/Bitcoin/*` implementations (no accidental base usage)
138. [ ] Add smoke tests that import and exercise Bitcoin consensus/block commit explicitly
139. [ ] Performance/observability
140. [ ] Basic profiling for proof generation, redaction voting, block processing
141. [ ] Toggleable detailed logging via config for demo/tests

### Important Notes

- Public EVM cannot delete transaction history/logs; redaction operates at application/data layer only
- Protocol-level redaction requires permissioned blockchain with chameleon-hash support
- Keep Python simulation as reliable fallback for development and testing
- Implement suggested order: IPFS → EVM → SNARKs for incremental progress
