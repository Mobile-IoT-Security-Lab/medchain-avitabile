Circuits and SNARK Pipeline (Scaffold)

This directory provides a minimal scaffold to start completing todo items 39–46.
It wires up a Circom circuit, Groth16 setup/prove/verify with snarkjs, and exports a Solidity verifier without changing existing contracts by default.

Prerequisites

- circom v2.x in PATH (https://docs.circom.io/getting-started/installation/)
- snarkjs available either:
  - locally in `contracts/node_modules/.bin/snarkjs` (run `cd contracts && npm i`), or
  - globally installed in PATH
- a Powers of Tau file, e.g. powersOfTau28_hez_final_12.ptau

Files

- `redaction.circom` – placeholder circuit exposing public inputs for policy hash, Merkle root, original/redacted hashes, and a policyAllowed flag. It enforces `policyAllowed == 1` and outputs a checksum. No real hash/Merkle computations yet.
- `scripts/compile.sh` – compiles the circuit to R1CS/WASM/SYM under `build/`.
- `scripts/setup.sh` – runs Groth16 setup + a contribution and exports a verification key.
- `scripts/prove.sh` – generates a witness, proof, and verifies it. Accepts an optional input JSON path; defaults to `input/example.json`.
- `scripts/export-verifier.sh` – exports the Solidity verifier to `contracts/src/RedactionVerifier_groth16.sol` and adds a `RedactionVerifier` alias wrapper.
- `scripts/clean.sh` – deletes the `build/` folder.
- `input/example.json` – sample inputs matching the placeholder circuit (policyAllowed=1).

Quickstart

1) Compile the circuit
   ./scripts/compile.sh

2) Run Groth16 setup (provide PTAU path if not placed in tools/)
   PTAU=tools/powersOfTau28_hez_final_12.ptau ./scripts/setup.sh

3) Generate a proof (uses input/example.json)
   ./scripts/prove.sh

4) Export a Solidity verifier (keeps existing stub intact)
   ./scripts/export-verifier.sh

5) Compile and test contracts
   cd ../contracts && npx hardhat compile && npx hardhat test

Notes

- The generated verifier is written to `contracts/src/RedactionVerifier_groth16.sol` to avoid breaking the existing stub (`RedactionVerifier.sol`) and its custom ABI.
  Integrating the generated verifier will require adjusting `MedicalDataManager.sol` to use the Groth16 `verifyProof` signature.
- To make #40–#43 real, replace the placeholder constraints with:
  - SHA256/Poseidon hash components for H(original)/H(redacted)
  - policy hash preimage computation/matching
  - optional Merkle membership verification (e.g., circomlib `MerkleTreeInclusionProof`)
- The Makefile offers wrappers for these scripts; see the repository root Makefile targets `circuits-*` after this scaffold.

