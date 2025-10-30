"""Redaction backend interface and implementations.

Provides a pluggable layer so the MyRedactionEngine can operate
against either the simulated in-memory contract or an EVM-backed adapter.

### Bookmark2 for next meeting - Phase 2 on-chain verification implementation
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

    Phase 2: Full on-chain verification with nullifier tracking and consistency proofs.
    """

    def __init__(self, evm_client: Any, contract: Any, nullifier_registry: Any = None, ipfs_manager: Any | None = None):
        self.evm = evm_client
        self.contract = contract
        self.nullifier_registry = nullifier_registry
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
            # If explicit legacy proof provided, use legacy path
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
            if proof_payload and (
                proof_payload.get("proof_json_path") or proof_payload.get("public_json_path")
            ):
                return self.evm.requestDataRedactionFromSnarkjs(
                    self.contract,
                    patient_id,
                    redaction_type,
                    reason,
                    proof_json_path=proof_payload.get("proof_json_path"),
                    public_json_path=proof_payload.get("public_json_path"),
                )
            # Auto-discover default paths under circuits/build if not provided explicitly
            return self.evm.requestDataRedactionAuto(
                self.contract,
                patient_id,
                redaction_type,
                reason,
            )
        except Exception:
            return None
    
    def request_data_redaction_with_full_proofs(
        self,
        patient_id: str,
        redaction_type: str,
        reason: str,
        snark_proof_payload: Dict[str, Any],
        consistency_proof: Any,
    ) -> Optional[str]:
        """Phase 2: Submit redaction request with full on-chain verification."""
        if self.contract is None or self.evm is None:
            return None
        
        try:
            # Extract nullifier from public signals
            pub_signals = snark_proof_payload.get("pubSignals", [])
            nullifier_bytes = b"\x00" * 32
            
            if len(pub_signals) >= 10:
                # Public signal indices 8 and 9 contain nullifier0 and nullifier1
                null_limb0 = int(pub_signals[8])
                null_limb1 = int(pub_signals[9])
                nullifier_int = null_limb0 + (null_limb1 << 128)
                nullifier_bytes = nullifier_int.to_bytes(32, 'big')
            
            # Compute consistency proof hash
            import json
            from web3 import Web3
            consistency_hash = Web3.keccak(
                text=json.dumps({
                    "pre_state_hash": consistency_proof.pre_state_hash if hasattr(consistency_proof, 'pre_state_hash') else "",
                    "post_state_hash": consistency_proof.post_state_hash if hasattr(consistency_proof, 'post_state_hash') else "",
                    "is_valid": consistency_proof.is_valid if hasattr(consistency_proof, 'is_valid') else True
                })
            )
            
            # Extract state hashes from public signals
            pre_state_hash = b"\x00" * 32
            post_state_hash = b"\x00" * 32
            
            if len(pub_signals) >= 14:
                # Indices 10, 11 = preStateHash0, preStateHash1
                # Indices 12, 13 = postStateHash0, postStateHash1
                pre_limb0 = int(pub_signals[10])
                pre_limb1 = int(pub_signals[11])
                pre_state_int = pre_limb0 + (pre_limb1 << 128)
                pre_state_hash = pre_state_int.to_bytes(32, 'big')
                
                post_limb0 = int(pub_signals[12])
                post_limb1 = int(pub_signals[13])
                post_state_int = post_limb0 + (post_limb1 << 128)
                post_state_hash = post_state_int.to_bytes(32, 'big')
            
            # Call the contract method with full proof verification
            return self.evm.requestDataRedactionWithFullProofs(
                self.contract,
                patient_id,
                redaction_type,
                reason,
                snark_proof_payload.get("pA", []),
                snark_proof_payload.get("pB", []),
                snark_proof_payload.get("pC", []),
                pub_signals,
                nullifier_bytes,
                consistency_hash,
                pre_state_hash,
                post_state_hash,
            )
        except Exception as e:
            print(f"Failed to submit full proofs on-chain: {e}")
            return None
        if self.contract is None or self.evm is None:
            return None
            
        try:
            import hashlib
            import time
            
            # Extract SNARK proof components
            pA = snark_proof_payload.get("pA", [])
            pB = snark_proof_payload.get("pB", [])
            pC = snark_proof_payload.get("pC", [])
            pubSignals = snark_proof_payload.get("pubSignals", [])
            
            # Extract or generate nullifier
            nullifier = snark_proof_payload.get("nullifier")
            if not nullifier:
                # Generate nullifier from proof data
                nullifier_str = f"{patient_id}_{int(time.time())}_{hash(str(pubSignals))}"
                nullifier = hashlib.sha256(nullifier_str.encode()).digest()
            else:
                # Ensure it's bytes32
                if isinstance(nullifier, str):
                    if nullifier.startswith("nullifier_"):
                        # Generate from string
                        nullifier = hashlib.sha256(nullifier.encode()).digest()
                    elif len(nullifier) == 64:
                        nullifier = bytes.fromhex(nullifier)
                    else:
                        nullifier = nullifier.encode()
                if not isinstance(nullifier, bytes):
                    nullifier = str(nullifier).encode()
                if len(nullifier) != 32:
                    nullifier = hashlib.sha256(nullifier).digest()
            
            # Check nullifier validity before submitting (if registry available)
            if self.nullifier_registry is not None:
                try:
                    nullifier_valid = self.nullifier_registry.functions.isNullifierValid(nullifier).call()
                    if not nullifier_valid:
                        print(f" Nullifier already used - replay attack prevented")
                        return None
                except Exception:
                    pass  # Registry may not be available
            
            # Extract consistency proof hashes
            if consistency_proof:
                # Compute consistency proof hash
                import json
                consistency_dict = {
                    "check_type": str(consistency_proof.check_type) if hasattr(consistency_proof, "check_type") else "",
                    "pre_state": str(consistency_proof.pre_redaction_state) if hasattr(consistency_proof, "pre_redaction_state") else "",
                    "post_state": str(consistency_proof.post_redaction_state) if hasattr(consistency_proof, "post_redaction_state") else "",
                }
                consistency_proof_hash = hashlib.sha256(json.dumps(consistency_dict, sort_keys=True).encode()).digest()
                
                # Compute state hashes
                if hasattr(consistency_proof, "pre_redaction_state"):
                    pre_state_str = json.dumps(consistency_proof.pre_redaction_state, sort_keys=True)
                    pre_state_hash = hashlib.sha256(pre_state_str.encode()).digest()
                else:
                    pre_state_hash = b'\x00' * 32
                    
                if hasattr(consistency_proof, "post_redaction_state"):
                    post_state_str = json.dumps(consistency_proof.post_redaction_state, sort_keys=True)
                    post_state_hash = hashlib.sha256(post_state_str.encode()).digest()
                else:
                    post_state_hash = b'\x00' * 32
            else:
                consistency_proof_hash = b'\x00' * 32
                pre_state_hash = b'\x00' * 32
                post_state_hash = b'\x00' * 32
            
            # Submit to smart contract with full proofs (Phase 2)
            fn = self.contract.functions.requestDataRedactionWithFullProofs(
                patient_id,
                redaction_type,
                reason,
                pA,
                pB,
                pC,
                pubSignals,
                nullifier,
                consistency_proof_hash,
                pre_state_hash,
                post_state_hash
            )
            
            tx_hash = self.evm._build_and_send(fn)
            
            if tx_hash:
                print(f" Phase 2 on-chain verification successful")
                print(f"   TX Hash: {tx_hash}")
                print(f"   Nullifier: {nullifier.hex()}")
                print(f"   Consistency Proof: {consistency_proof_hash.hex()[:16]}...")
                return tx_hash
            
            return None
            
        except Exception as exc:
            print(f" Phase 2 on-chain verification failed: {exc}")
            import traceback
            traceback.print_exc()
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
