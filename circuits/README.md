# Circuits and SNARK Pipeline

This directory implements todo items 39–43:

- A working Circom circuit with real constraints for H(original), H(redacted), policy hash matching, and an optional Merkle inclusion proof (MiMC-based, demo-friendly).
- Scripts to compile, run Groth16 setup/prove/verify with snarkjs, and export a Solidity verifier without changing existing stubs by default.

Prerequisites

- circom v2.x in PATH (<https://docs.circom.io/getting-started/installation/>)
- snarkjs available either:
  - locally in `contracts/node_modules/.bin/snarkjs` (run `cd contracts && npm i`), or
  - globally installed in PATH
- a Powers of Tau file. For this circuit size (~6802 constraints), use power ≥ 14
  (e.g. tools/pot14_final.ptau). Power 12 is insufficient (2^12 < 2×constraints).

Files

- `redaction.circom` – circuit that:
  - computes `H(original)` and `H(redacted)` using a MiMC-like permutation over field elements;
  - matches the policy hash against a MiMC hash of a policy preimage;
  - optionally enforces a Merkle inclusion proof of `H(original)` when `enforceMerkle=1` using a MiMC-based binary Merkle tree;
  - keeps `policyAllowed` as a public boolean gate (demo semantics) and outputs a checksum.
- `scripts/compile.sh` – compiles the circuit to R1CS/WASM/SYM under `build/`.
- `scripts/setup.sh` – runs Groth16 setup + a contribution and exports a verification key.
- `scripts/prove.sh` – generates a witness, proof, and verifies it. Accepts an optional input JSON path; defaults to `input/example.json`.
- `scripts/export-verifier.sh` – exports the Solidity verifier to `contracts/src/RedactionVerifier_groth16.sol` and adds a `RedactionVerifier` alias wrapper.
- `scripts/clean.sh` – deletes the `build/` folder.
- `input/example.json` – sample inputs matching the placeholder circuit (policyAllowed=1).

Quickstart

1) Compile the circuit
   ./scripts/compile.sh

2) Run Groth16 setup (provide PTAU path; power ≥ 14 recommended)
   PTAU=tools/pot14_final.ptau ./scripts/setup.sh

3) Generate a proof (uses input/example.json)
   ./scripts/prove.sh

4) Export a Solidity verifier (keeps existing stub intact)
   ./scripts/export-verifier.sh

5) Compile and test contracts
   cd ../contracts && npx hardhat compile && npx hardhat test

Notes

- The generated verifier is written to `contracts/src/RedactionVerifier_groth16.sol` to avoid breaking the existing stub (`RedactionVerifier.sol`) and its custom ABI.
  Integrating the generated verifier will require adjusting `MedicalDataManager.sol` to use the Groth16 `verifyProof` signature.
- Hash/Merkle are implemented with a MiMC-style permutation and zero round constants to keep `H(0,...,0)=0` for the example vectors. Replace with standard constants or Poseidon for production.
- Inputs now include private arrays: `originalData[]`, `redactedData[]`, `policyData[]`, optional `merklePathElements[]`, `merklePathIndices[]`, and `enforceMerkle`.
- The Makefile offers wrappers for these scripts; see the repository root Makefile targets `circuits-*` after this scaffold.
