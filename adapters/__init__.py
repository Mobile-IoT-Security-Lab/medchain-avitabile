"""Backend adapter package for real EVM/SNARK/IPFS integrations.

Default repo behavior remains simulated. Flip env flags to use real backends:
- USE_REAL_IPFS=1
- USE_REAL_EVM=1
- USE_REAL_SNARK=1
"""

__all__ = [
    "config",
]

