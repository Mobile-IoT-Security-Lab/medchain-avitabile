"""Redaction backend interface and implementations.

Provides a pluggable layer so the MyRedactionEngine can operate
against either the simulated in-memory contract or an EVM-backed adapter.
"""
from __future__ import annotations

from typing import Optional, Any, Dict


class RedactionBackend:
    """Abstract backend for redaction flows."""

    def store_medical_data(self, record: Any) -> bool:
        raise NotImplementedError

    def request_data_redaction(
        self,
        patient_id: str,
        redaction_type: str,
        reason: str,
        proof_payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        raise NotImplementedError

    def approve_redaction(self, request_id: str | int, approver: str, comments: str = "") -> bool:
        raise NotImplementedError

    def execute_redaction(self, request_id: str | int) -> bool:
        raise NotImplementedError

    def query_medical_data(self, patient_id: str, requester: str) -> Optional[Any]:
        raise NotImplementedError

    def get_redaction_history(self, patient_id: Optional[str] = None) -> list[Dict[str, Any]]:
        raise NotImplementedError


class SimulatedBackend(RedactionBackend):
    """Pass-through backend delegating to the engine's simulated logic."""

    def __init__(self, engine: Any):
        self.engine = engine

    def store_medical_data(self, record: Any) -> bool:
        return self.engine.store_medical_data(record)

    def request_data_redaction(
        self,
        patient_id: str,
        redaction_type: str,
        reason: str,
        proof_payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        return self.engine.request_data_redaction(patient_id, redaction_type, reason, requester="backend")

    def approve_redaction(self, request_id: str | int, approver: str, comments: str = "") -> bool:
        return self.engine.approve_redaction(str(request_id), approver, comments)

    def execute_redaction(self, request_id: str | int) -> bool:
        return self.engine.execute_redaction(str(request_id))

    def query_medical_data(self, patient_id: str, requester: str) -> Optional[Any]:
        return self.engine.query_medical_data(patient_id, requester)

    def get_redaction_history(self, patient_id: Optional[str] = None) -> list[Dict[str, Any]]:
        return self.engine.get_redaction_history(patient_id)


class EVMBackend(RedactionBackend):
    """Backend that mirrors requests to an EVM contract via the adapter.

    Note: execution remains off-chain/simulated; this backend emits requests/approvals on-chain.
    """

    def __init__(self, evm_client: Any, contract: Any, ipfs_manager: Any | None = None):
        self.evm = evm_client
        self.contract = contract
        self.ipfs_manager = ipfs_manager

    def store_medical_data(self, record: Any) -> bool:
        # No-op: pointer writes are performed in the demo, not directly from the engine.
        return True

    def request_data_redaction(
        self,
        patient_id: str,
        redaction_type: str,
        reason: str,
        proof_payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if self.contract is None or self.evm is None:
            return None
        try:
            if proof_payload and proof_payload.get("proof") is not None:
                return self.evm.requestDataRedactionWithProof(
                    self.contract,
                    patient_id,
                    redaction_type,
                    reason,
                    proof_payload.get("proof", b""),
                    proof_payload.get("policy_hash", b"\x00" * 32),
                    proof_payload.get("merkle_root", b"\x00" * 32),
                    proof_payload.get("original_hash", b"\x00" * 32),
                    proof_payload.get("redacted_hash", b"\x00" * 32),
                )
            else:
                return self.evm.requestDataRedaction(self.contract, patient_id, redaction_type, reason)
        except Exception:
            return None

    def approve_redaction(self, request_id: str | int, approver: str, comments: str = "") -> bool:
        if self.contract is None or self.evm is None:
            return False
        try:
            req_int = int(request_id) if not isinstance(request_id, int) else request_id
            return bool(self.evm.approveRedaction(self.contract, req_int))
        except Exception:
            return False

    def execute_redaction(self, request_id: str | int) -> bool:
        # Off-chain in this architecture
        return False

    def query_medical_data(self, patient_id: str, requester: str) -> Optional[Any]:
        # On-chain data is only a pointer; engine handles querying own state.
        return None

    def get_redaction_history(self, patient_id: Optional[str] = None) -> list[Dict[str, Any]]:
        # Events should be queried by higher-level code if needed.
        return []
