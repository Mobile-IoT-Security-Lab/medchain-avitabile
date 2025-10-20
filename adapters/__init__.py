"""Backend adapter package for real EVM/SNARK/IPFS integrations.

Default repo behavior remains simulated except for SNARK proofs, which always
use the real snarkjs pipeline. Optional flags:
- USE_REAL_IPFS=1
- USE_REAL_EVM=1
"""

__all__ = [
    "config",
]
