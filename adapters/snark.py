"""SNARK adapter scaffold (future work).

Wrap circom/snarkjs for witness/proof generation and formatting calldata for Solidity verifier.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from .config import env_bool


class SnarkClient:
    """Placeholder SNARK client. Wire up in a later step with snarkjs CLI bindings.
    Intended methods:
      - generate_witness(public_inputs, private_inputs)
      - prove(witness) -> (proof, public_signals)
      - format_calldata(proof, public_signals)
    """

    def is_enabled(self) -> bool:
        return env_bool("USE_REAL_SNARK", False)

    def prove_redaction(self, public_inputs: Dict[str, Any], private_inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: implement using snarkjs
        return None

