"""EVM adapter scaffold (future work).

Provides a minimal interface; real implementation will use web3.py and deployed contracts.
"""
from __future__ import annotations

from typing import Any, Optional
from .config import env_bool, env_str


class EVMClient:
    """Placeholder EVM client. Wire up in a later step.

    Intended methods:
      - connect(provider_url)
      - deploy_medical_contract(...)
      - load_contract(abi, address)
      - storeMedicalData(...)
      - requestDataRedaction(...)
      - approveRedaction(...)
      - executeRedaction(...)
    """

    def __init__(self) -> None:
        self._connected = False

    def is_enabled(self) -> bool:
        return env_bool("USE_REAL_EVM", False)

    def connect(self) -> bool:
        # TODO: implement with web3.py
        self._connected = False
        return False

