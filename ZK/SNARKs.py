"""
SNARKs (Zero-Knowledge Succinct Non-Interactive Arguments of Knowledge) Implementation
for Data Redaction in Smart-Contract-Enabled Permissioned Blockchains

This module implements zk-SNARKs to provide privacy-preserving proofs for redaction operations
while maintaining blockchain consistency and auditability.

### Bookmark1 for next meeting
"""

import hashlib
import json
import random
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from medical.circuit_mapper import MedicalDataCircuitMapper

# Use built-in hashlib instead of external crypto libraries for compatibility

@dataclass
class ZKProof:
    """Zero-knowledge proof structure for redaction operations."""
    proof_id: str
    operation_type: str  # "DELETE", "MODIFY", "ANONYMIZE"
    commitment: str  # Commitment to the redacted data
    nullifier: str  # Prevents double-spending/double-redaction
    merkle_root: str  # Merkle root of the valid state
    timestamp: int
    verifier_challenge: str
    prover_response: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RedactionCommitment:
    """Commitment structure for redaction proofs."""
    original_hash: str
    redacted_hash: str
    operation_hash: str
    randomness: str
    timestamp: int

    #         results[proof.proof_id] = self.verify_proof(proof, public_inputs)
            
    #     return results


class RedactionSNARKManager:
    """
    High-level manager for redaction proofs backed by real snarkjs circuits.
    """
    
    def __init__(self, snark_client: Optional[Any] = None):
        if snark_client is None:
            from adapters.snark import SnarkClient
            snark_client = SnarkClient()
        if not hasattr(snark_client, "is_available") or not snark_client.is_available():
            raise ValueError("SnarkClient must expose circuit artifacts to generate proofs")
        
        self.snark_client = snark_client
        self.circuit_mapper = MedicalDataCircuitMapper()
        self.commitment_store: Dict[str, RedactionCommitment] = {}
    
    def _extract_medical_record_dict(self, redaction_request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medical record information from a redaction request."""
        original_data = redaction_request.get("original_data", "{}")
        try:
            record_dict = json.loads(original_data)
            if isinstance(record_dict, dict) and "patient_id" in record_dict:
                return record_dict
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "patient_id": redaction_request.get("request_id", "unknown"),
            "diagnosis": original_data if isinstance(original_data, str) else str(original_data),
            "treatment": "",
            "physician": redaction_request.get("requester", "unknown")
        }
    
    def _compute_operation_hash(self, redaction_request: Dict[str, Any]) -> str:
        """Compute a deterministic hash describing the redaction operation."""
        try:
            payload = json.dumps(redaction_request, sort_keys=True, default=str)
        except TypeError:
            payload = str(redaction_request)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def create_redaction_proof(self, redaction_request: Dict[str, Any]) -> Optional[ZKProof]:
        """
        Create a SNARK proof for a redaction request using real snarkjs artifacts.
        """
        try:
            medical_record = self._extract_medical_record_dict(redaction_request)
            redaction_type = redaction_request.get("redaction_type", "MODIFY")
            policy_hash = redaction_request.get("policy_hash", f"policy_{redaction_type}")
            
            # Prepare circuit inputs
            circuit_inputs = self.circuit_mapper.prepare_circuit_inputs(
                medical_record,
                redaction_type,
                policy_hash
            )
            if not self.circuit_mapper.validate_circuit_inputs(circuit_inputs):
                raise ValueError("Invalid circuit inputs generated for redaction proof")
            
            result = self.snark_client.prove_redaction(
                circuit_inputs.public_inputs,
                circuit_inputs.private_inputs
            )
            if not result or not result.get("verified"):
                raise ValueError("snarkjs failed to generate a verified proof")
            
            calldata = result.get("calldata", {})
            pub_signals = calldata.get("pubSignals", [])
            if not pub_signals:
                raise ValueError("Missing public signals from snarkjs result")
            
            proof_id = f"real_{int(time.time())}_{hash(str(pub_signals)) % 1_000_000}"
            proof = ZKProof(
                proof_id=proof_id,
                operation_type=redaction_type,
                commitment=str(pub_signals[0]),
                nullifier=f"nullifier_{int(time.time())}",
                merkle_root=str(circuit_inputs.public_inputs.get("merkleRoot0", 0)),
                timestamp=int(time.time()),
                verifier_challenge=json.dumps(result.get("proof", {})),
                prover_response=json.dumps(pub_signals)
            )
            
            original_serialized = self.circuit_mapper.serialize_medical_data(medical_record)
            redacted_serialized = self.circuit_mapper.apply_redaction(original_serialized, redaction_type)
            commitment = RedactionCommitment(
                original_hash=hashlib.sha256(original_serialized.encode()).hexdigest(),
                redacted_hash=hashlib.sha256(redacted_serialized.encode()).hexdigest(),
                operation_hash=self._compute_operation_hash(redaction_request),
                randomness=str(random.randint(1, 2**128)),
                timestamp=proof.timestamp
            )
            self.commitment_store[proof.proof_id] = commitment
            return proof
        except Exception as exc:
            print(f" Failed to create real SNARK proof: {exc}")
            return None
    
    def verify_redaction_proof(self, proof: ZKProof, public_inputs: Dict[str, Any]) -> bool:
        """Verify a redaction proof using snarkjs verification."""
        try:
            proof_payload = json.loads(proof.verifier_challenge)
            public_signals = json.loads(proof.prover_response)
            return self.snark_client.verify_proof(proof_payload, public_signals)
        except Exception as exc:
            print(f" Proof verification error for {proof.proof_id}: {exc}")
            return False
        
    def get_commitment(self, proof_id: str) -> Optional[RedactionCommitment]:
        """Get stored commitment for a proof."""
        return self.commitment_store.get(proof_id)
        
    def audit_redaction_history(self, proof_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Audit redaction history using stored commitments."""
        audit_results: Dict[str, Dict[str, Any]] = {}
        
        for proof_id in proof_ids:
            commitment = self.get_commitment(proof_id)
            if commitment:
                audit_results[proof_id] = {
                    "commitment": asdict(commitment),
                    "status": "VALID",
                    "audit_timestamp": int(time.time())
                }
            else:
                audit_results[proof_id] = {
                    "status": "NOT_FOUND",
                    "audit_timestamp": int(time.time())
                }
                
        return audit_results


# Example usage and testing
def test_snark_system():
    """Test the SNARK system with sample redaction operations."""
    print("\n Testing SNARK System for Redaction Operations")
    print("=" * 60)
    
    try:
        manager = RedactionSNARKManager()
    except Exception as exc:
        print(f" Unable to initialize real SNARK manager: {exc}")
        return
    
    # Test redaction request
    redaction_request = {
        "request_id": "req_123456",
        "redaction_type": "ANONYMIZE",
        "target_block": 10,
        "target_tx": 2,
        "requester": "regulator_001",
        "requester_role": "REGULATOR",
        "original_data": "Patient John Doe, SSN: 123-45-6789",
        "redacted_data": "Patient [REDACTED], SSN: [REDACTED]",
        "merkle_root": "abcd1234efgh5678",
        "policy_hash": "policy_gdpr_001",
        "signature": "sig_abcd1234"
    }
    
    # Create proof
    proof = manager.create_redaction_proof(redaction_request)
    
    if proof:
        print(f"\n Proof Details:")
        print(f"  ID: {proof.proof_id}")
        print(f"  Operation: {proof.operation_type}")
        print(f"  Timestamp: {proof.timestamp}")
        print(f"  Commitment: {proof.commitment[:16]}...")
        print(f"  Nullifier: {proof.nullifier[:16]}...")
        
        # Verify proof
        public_inputs = {
            "operation_type": "ANONYMIZE",
            "target_block": 10,
            "target_tx": 2,
            "merkle_root": "abcd1234efgh5678",
            "policy_hash": "policy_gdpr_001"
        }
        
        is_valid = manager.verify_redaction_proof(proof, public_inputs)
        print(f"\n Verification Result: {' VALID' if is_valid else ' INVALID'}")
        
        # Test audit
        audit_results = manager.audit_redaction_history([proof.proof_id])
        print(f"\n Audit Results:")
        for proof_id, result in audit_results.items():
            print(f"  {proof_id}: {result['status']}")
    
    print("\n SNARK system test completed!")


if __name__ == "__main__":
    test_snark_system()
