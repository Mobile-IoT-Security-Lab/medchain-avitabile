"""
Enhanced Hybrid SNARK Manager with Circuit Mapper Integration
=============================================================

This module provides an improved HybridSNARKManager that uses the
MedicalDataCircuitMapper to properly prepare circuit inputs for real
SNARK proof generation.


### Bookmark1 for next meeting
"""

import json
import time
from typing import Dict, Any, Optional

from ZK.SNARKs import ZKProof

try:
    from medical.circuit_mapper import MedicalDataCircuitMapper
except ImportError:
    MedicalDataCircuitMapper = None  # type: ignore

try:
    from adapters.snark import SnarkClient
except ImportError:
    SnarkClient = None  # type: ignore


class EnhancedHybridSNARKManager:
    """
    Hybrid SNARK manager that integrates circuit mapper for real proof generation.
    
    This manager:
    1. Uses MedicalDataCircuitMapper to prepare proper circuit inputs
    2. Generates real Groth16 proofs via snarkjs
    3. Provides detailed diagnostics for proof generation
    """
    
    def __init__(self, snark_client: Optional[Any] = None):
        """
        Initialize the my hybrid SNARK manager.
        
        Args:
            snark_client: Optional SnarkClient instance for real proof generation
        """
        if snark_client is None:
            from adapters.snark import SnarkClient
            snark_client = SnarkClient()
        if not hasattr(snark_client, 'is_available') or not snark_client.is_available():
            raise ValueError("EnhancedHybridSNARKManager requires a ready SnarkClient with circuit artifacts")
        if MedicalDataCircuitMapper is None:
            raise ImportError("MedicalDataCircuitMapper is required for real SNARK proofs")

        self.snark_client = snark_client
        self.circuit_mapper = MedicalDataCircuitMapper()
    
    def _extract_medical_record_dict(self, redaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract medical record dictionary from redaction data.
        
        Args:
            redaction_data: Redaction request data
            
        Returns:
            Medical record as dictionary
        """
        original_data = redaction_data.get("original_data", "{}")
        
        try:
            # Try to parse as JSON (from medical record)
            record_dict = json.loads(original_data)
            
            # If it's already a complete dict, use it
            if isinstance(record_dict, dict) and "patient_id" in record_dict:
                return record_dict
                
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback: construct minimal record
        return {
            "patient_id": redaction_data.get("request_id", "unknown"),
            "diagnosis": original_data if isinstance(original_data, str) else str(original_data),
            "treatment": "",
            "physician": redaction_data.get("requester", "unknown")
        }
    
    def create_redaction_proof(self, redaction_data: Dict[str, Any]) -> Optional[ZKProof]:
        """
        Create a redaction proof using real snarkjs or simulation.
        
        Args:
            redaction_data: Dictionary containing redaction request details
            
        Returns:
            ZKProof object if successful, None otherwise
        """
        try:
            print(f" Generating real SNARK proof...")
            
            # Extract medical record
            medical_record_dict = self._extract_medical_record_dict(redaction_data)
            
            # Get redaction type and policy
            redaction_type = redaction_data.get("redaction_type", "MODIFY")
            policy_hash = redaction_data.get("policy_hash", f"policy_{redaction_type}")
            
            # Use circuit mapper to prepare inputs
            circuit_inputs = self.circuit_mapper.prepare_circuit_inputs(
                medical_record_dict,
                redaction_type,
                policy_hash
            )
            
            # Validate inputs
            if not self.circuit_mapper.validate_circuit_inputs(circuit_inputs):
                print(f"  Circuit input validation failed")
                raise ValueError("Invalid circuit inputs")
            
            print(f"   Circuit inputs prepared and validated")
            
            # Generate real SNARK proof using snarkjs
            result = self.snark_client.prove_redaction(
                circuit_inputs.public_inputs,
                circuit_inputs.private_inputs
            )
            
            if not result or not result.get("verified"):
                print(f"  Real SNARK proof verification failed")
                raise ValueError("Proof verification failed")
            
            # Extract calldata
            calldata = result.get("calldata", {})
            pub_signals = calldata.get("pubSignals", [])
            if not pub_signals:
                raise ValueError("Missing public signals from proof result")
            
            # Create ZKProof object compatible with existing system
            proof = ZKProof(
                proof_id=f"real_groth16_{int(time.time())}_{hash(str(pub_signals)) % 10000}",
                operation_type=redaction_type,
                commitment=str(pub_signals[0]),
                nullifier=f"nullifier_real_{int(time.time())}",
                merkle_root=str(circuit_inputs.public_inputs.get("merkleRoot0", 0)),
                timestamp=int(time.time()),
                verifier_challenge=json.dumps(result.get("proof", {})),
                prover_response=json.dumps(pub_signals)
            )
            
            return proof
            
        except Exception as e:
            print(f"  Real SNARK proof generation failed: {e}")
            return None
    
    def create_redaction_proof_with_consistency(
        self,
        redaction_data: Dict[str, Any],
        consistency_proof=None  # Optional ConsistencyProof
    ) -> Optional[ZKProof]:
        """
        Create a redaction proof WITH consistency verification integrated.
        
        Args:
            redaction_data: Dictionary containing redaction request details
            consistency_proof: Optional ConsistencyProof object to integrate
            
        Returns:
            ZKProof object if successful, None otherwise
        """
        try:
            print(f" Generating real SNARK proof WITH consistency verification...")
            
            # Extract medical record
            medical_record_dict = self._extract_medical_record_dict(redaction_data)
            
            # Get redaction type and policy
            redaction_type = redaction_data.get("redaction_type", "MODIFY")
            policy_hash = redaction_data.get("policy_hash", f"policy_{redaction_type}")
            
            # Generate nullifier
            import hashlib
            nullifier_seed = f"{redaction_data.get('request_id', 'unknown')}_{int(time.time())}"
            nullifier = hashlib.sha256(nullifier_seed.encode()).hexdigest()
            
            # Extract consistency proof data
            consistency_data = None
            if consistency_proof:
                consistency_data = {
                    "pre_state_hash": consistency_proof.pre_state_hash if hasattr(consistency_proof, 'pre_state_hash') else "0" * 64,
                    "post_state_hash": consistency_proof.post_state_hash if hasattr(consistency_proof, 'post_state_hash') else "0" * 64,
                    "valid": consistency_proof.is_valid if hasattr(consistency_proof, 'is_valid') else True
                }
            
            # Use circuit mapper to prepare inputs WITH consistency proof
            circuit_inputs = self.circuit_mapper.prepare_circuit_inputs(
                medical_record_dict,
                redaction_type,
                policy_hash,
                consistency_proof=consistency_data,
                nullifier=nullifier
            )
            
            # Validate inputs with consistency
            if not self.circuit_mapper.validate_circuit_inputs(circuit_inputs):
                print(f"  Circuit input validation failed (with consistency)")
                raise ValueError("Invalid circuit inputs with consistency")
            
            print(f"   Circuit inputs prepared and validated (with consistency)")
            
            # Generate real SNARK proof using snarkjs
            result = self.snark_client.prove_redaction(
                circuit_inputs.public_inputs,
                circuit_inputs.private_inputs
            )
            
            if not result or not result.get("verified"):
                print(f"  Real SNARK proof verification failed")
                raise ValueError("Proof verification failed")
            
            # Extract calldata
            calldata = result.get("calldata", {})
            pub_signals = calldata.get("pubSignals", [])
            if not pub_signals:
                raise ValueError("Missing public signals from proof result")
            
            # Extract nullifier from public signals (indices 8, 9 based on our circuit)
            # Public signal order: policyHash0, policyHash1, merkleRoot0, merkleRoot1,
            #                      originalHash0, originalHash1, redactedHash0, redactedHash1,
            #                      nullifier0, nullifier1, preStateHash0, preStateHash1,
            #                      postStateHash0, postStateHash1, consistencyCheckPassed, policyAllowed
            nullifier_from_proof = None
            if len(pub_signals) >= 10:
                # Reconstruct nullifier from limbs (indices 8 and 9)
                null_limb0 = int(pub_signals[8])
                null_limb1 = int(pub_signals[9])
                nullifier_int = null_limb0 + (null_limb1 << 128)
                nullifier_from_proof = hex(nullifier_int)[2:].zfill(64)
            
            # Create ZKProof object compatible with existing system
            proof = ZKProof(
                proof_id=f"real_groth16_consistency_{int(time.time())}_{hash(str(pub_signals)) % 10000}",
                operation_type=redaction_type,
                commitment=str(pub_signals[0]),
                nullifier=nullifier_from_proof or f"nullifier_{nullifier[:16]}",
                merkle_root=str(circuit_inputs.public_inputs.get("merkleRoot0", 0)),
                timestamp=int(time.time()),
                verifier_challenge=json.dumps(result.get("proof", {})),
                prover_response=json.dumps(pub_signals)
            )
            
            return proof
            
        except Exception as e:
            print(f"  Real SNARK proof with consistency generation failed: {e}")
            return None
    
    def verify_redaction_proof(self, proof: ZKProof, public_inputs: Dict[str, Any]) -> bool:
        """
        Verify a redaction proof.
        
        Args:
            proof: ZKProof to verify
            public_inputs: Public inputs for verification
            
        Returns:
            True if proof is valid, False otherwise
        """
        try:
            proof_payload = json.loads(proof.verifier_challenge)
            public_signals = json.loads(proof.prover_response)
            is_valid = self.snark_client.verify_proof(proof_payload, public_signals)
            if not is_valid:
                print(f" Proof {proof.proof_id} failed verification")
            return is_valid
        except Exception as e:
            print(f" Verification error for proof {proof.proof_id}: {e}")
            return False
    
    def get_proof_metadata(self, proof: ZKProof) -> Dict[str, Any]:
        """
        Get metadata about a proof.
        
        Args:
            proof: ZKProof to get metadata for
            
        Returns:
            Dictionary with proof metadata
        """
        return {
            "proof_id": proof.proof_id,
            "operation_type": proof.operation_type,
            "mode": "REAL_GROTH16",
            "timestamp": proof.timestamp,
            "commitment": proof.commitment,
            "nullifier": proof.nullifier,
            "merkle_root": proof.merkle_root
        }
    
    def is_real_mode_available(self) -> bool:
        """
        Check if real SNARK mode is available.
        
        Returns:
            True if real mode is available, False otherwise
        """
        return True
    
    def get_mode_info(self) -> Dict[str, Any]:
        """
        Get information about current operation mode.
        
        Returns:
            Dictionary with mode information
        """
        return {
            "mode": "REAL",
            "backend": "circom/snarkjs",
            "circuit": "redaction.circom",
            "proof_system": "Groth16",
            "circuit_mapper": "enabled"
        }


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Enhanced Hybrid SNARK Manager Test")
    print("="*60)
    
    # Test with simulation mode
    print("\n1. Testing SIMULATION mode:")
    manager = EnhancedHybridSNARKManager()
    print(f"   Mode info: {manager.get_mode_info()}")
    
    # Create test redaction request
    test_request = {
        "request_id": "test_req_001",
        "redaction_type": "ANONYMIZE",
        "original_data": json.dumps({
            "patient_id": "PAT_001",
            "diagnosis": "Sensitive diagnosis",
            "treatment": "Sensitive treatment",
            "physician": "Dr. Test"
        }),
        "requester": "admin",
        "policy_hash": "policy_anonymize"
    }
    
    # Generate proof
    proof = manager.create_redaction_proof(test_request)
    if proof:
        print(f"\n Proof generated successfully")
        metadata = manager.get_proof_metadata(proof)
        print(f"   Proof metadata:")
        for key, value in metadata.items():
            print(f"     - {key}: {value}")
        
        # Verify proof
        public_inputs = {
            "operation_type": "ANONYMIZE",
            "merkle_root": "test_root",
            "policy_hash": "policy_anonymize"
        }
        is_valid = manager.verify_redaction_proof(proof, public_inputs)
        print(f"\n   Verification result: {' VALID' if is_valid else ' INVALID'}")
    else:
        print(f"\n Proof generation failed")
    
    print("\n" + "="*60)
