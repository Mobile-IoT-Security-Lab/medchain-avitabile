# NotebookLM Mind Map — Text Outline

## Definition

- Re-write blocks
- Compress blocks
- Insert blocks
- Authorized entities
- Publicly auditable
- New miners oblivious (history-independent)

## Reasons For Redaction (Editable Blockchain)

- Remove inappropriate content (e.g., child pornography, illegal data)
- Support re-writable storage applications
- “Right to be forgotten” (GDPR, GLBA, SEC Reg S‑P)
- Financial institution consolidation (reduce cost, increase trust)
- Scalability (compress blocks, save disk space)

## Concept & Motivation

- Immutability is contentious (e.g., DAO attack aftermath)
- Append-only is not suitable for all applications
- Abuse of arbitrary message storage
- Does not scale for smart-contract amendments/patches
- Limitations of immutability:
  - Permanent storage/perfect accountability issues
  - Difficulty in financial consolidation
  - Privacy and scalability impacts

## Comparison To Hard Forks

- Redactions intended for rare, exceptional circumstances
- Hard forks suit only recent blocks (“undo” operation)
- Hard-forking old blocks is costly/impractical
- Redaction mechanism helps with later-discovered errors/frauds

## Core Technology: Chameleon Hashes

- Cryptographic hash with trapdoor
  - Collision resistance without trapdoor
  - Efficient collision generation with trapdoor
- Standard CH issue: observing a collision reveals the trapdoor (key exposure)
- Need enhanced collision resistance
- Secret-coin CH:
  - Random coins used for hashing are secret
  - Verification via a dedicated verifier function; check value equals the randomness r
  - Hash is deterministic given message m and coins r
- Public-coin CH:
  - Verification by re-running the hash algorithm
  - No need to store h explicitly
- Generic transformation for enhanced collision resistance
  - Based on public-key encryption (CPA-secure)

## Ingredients

- Non-Interactive Zero-Knowledge (NIZK)
- Public-coin, collision-resistant CH
- Chameleon Hash Transform (our contribution)
- Instantiations and assumptions:
  - ROM: DDH
  - Standard model: k-Linear (pairing-based)
- Replace inner hash function G with a chameleon hash

## Integration Into Blockchain (General)

- History-independent blockchain
- Minimal changes to client software and data structures
- Single trusted authority initially holds trapdoor key
- Extended block: `B = <s, x, ctr, (h, σ)>`

## Rewriting And Removal Algorithms

- Rewriting blocks (Algorithm 1): compute collision with new content
- Shrinking chain (Algorithm 2): remove blocks, redact subsequent block, broadcast new chain
- Requires CH with key-exposure freeness

## Centralized vs. Decentralized Key Management

- Centralized: single authority holds trapdoor key
- Decentralized:
  - Trapdoor key shared among fixed users; MPC for redaction
  - Distributed key generation: produce `(hk, tk)`; share `tk`
  - Collision-finding: reconstruct `tk`, compute collision, distribute result
  - Security models:
    - Semi-honest: `(n−1)`-out-of-`n` secret sharing
    - Malicious: robust secret sharing (e.g., Shamir)
  - Concrete CH instantiation: Ateniese/de Medeiros

## Deployment Models

- Private blockchain: central authority holds trapdoor key; write permissions centralized
- Consortium blockchain: trapdoor shared among consortium parties; redactions via MPC
- Public blockchain (e.g., Bitcoin): trapdoor shared among chosen subset (e.g., mining pools)
- Built on Bitcoin Core v0.12

## Proof-of-Concept (Bitcoin Core)

- Implemented in centralized setting (single node holds key)
- Uses OpenSSL Bignum (C/C++)
- Functions: `GenerateKey`, `ChameleonHash`, `HashCollision`
- Extended class: `CBlockHeader` (`RandomnessR`, `RandomnessS`)
- Overloaded `SerializeHash`; modified `CreateNewBlock`
- New genesis block for the redactable chain
- `CChain` methods: `RedactBlock`, `RemoveBlock`
- Regression test network
- Performance: block creation overhead negligible (near-constant vs. Bitcoin Core)

## Performance & Challenges

- Block redaction/removal time independent of chain length; depends on block size
- Smart contracts not considered in basic scheme; redaction may break contract logic
- Prior challenge (Ateniese et al.): naive repeated redaction is harmful and non-scaling

## Our SNARK-Based Solution

- Use SNARKs to provide proofs
- Introduce Proof-of-Consistency
- Maintain state consistency after redaction
- Preserve public verifiability

## Redaction In Smart-Contract-Enabled Blockchains

- Modified transaction `t`
- SNARK for relation `R` with states `st` and `st″`
- Statement includes:
  - Block head `s`
  - Chameleon hash `h` and public key `hk`
  - Original transaction set `x`
- Witness includes: redacted transaction `tx`
- Proves:
  - `f(tx, st) = st′` and continued execution leads to `st″`
  - `Hash(hk, (s, x))` remains consistent with `(h, ·)`
  - An intermediate state `st′` exists linking old and new executions

## New Redaction Algorithm (for Smart Contracts)

- Generate new collision for the redacted block
- Generate proofs-of-consistency for subsequent transactions
- Auxiliary redaction information `IT` carries the proofs
- Desired properties:
  - Chain growth (unchanged hash value)
  - Chain consistency (states consistent with original data/proofs)
  - Privacy of original data (zero-knowledge via SNARKs)
  - Minimal-impact redaction (only direct fixes)

## Blockchain Basics

- Series of ordered blocks
- Each block links to previous via a hash
- Block: `B = <s, x, ctr>`
  - `s`: block head
  - `x`: set of transactions
  - `ctr`: nonce
- Valid block predicate defined by consortium
- P2P electronic cash system

## Bitcoin Specifics

- Block ID: double SHA-256 of header
- Proof-of-Work: increment nonce until `hash < target D`
- Miner builds blocks from valid transactions

## Smart Contracts

- State evolves with each input
- Current state inferred from blockchain

## Transaction Types (for Smart Contracts)

- Standard transactions: `(addr_tx, data, toaddr)`
- Smart contract transactions: `(addr_φ, f1…fl, initial state st0_φ)`

## Related Work

- Ateniese et al. (2017): seminal, CH for permissioned
- Puddu et al. (2017): chain mutations, user-defined, PoW voting, permissionless
- Deuber et al. (2019): proposals on-chain, voting, permissionless
- Thyagarajan et al. (2021): Reparo, enhances Deuber, permissionless
- Grigoriev et al. (2021): RSA-based, permissioned, similar issues to Ateniese
- Botta et al. (2022): SNARKs for local data redaction in Bitcoin (irrelevant data)
- Zhang et al. (2023): enhanced Ateniese with attribute-based encryption
- Zhou et al. (2023): fine-grained, owner/regulator; per-user CH
- Peng et al. (2023): voting, aggregate signature, off-chain proposal
- Wang et al. (2023): verifiable delay functions; supervisor-driven chain fork
- Dai et al. (2024): voting + chameleon hash for block substitution
- Other works: Ma et al., Wu et al., Dong et al., Larraia et al.
