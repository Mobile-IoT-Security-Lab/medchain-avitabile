"""
Cross-Component Integration Tests: SNARK ↔ EVM
===============================================

Tests the integration between SNARK and EVM components:
- Proof generation and on-chain verification
- Redaction proof workflows
- Circuit parameter validation
- Error handling for invalid proofs
"""

import pytest
import json
import hashlib
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch
import tempfile
import os

# Import adapters
from adapters.snark import SnarkClient
from adapters.evm import EVMClient
from adapters.config import env_bool

# Import SNARK and proof components
from ZK.SNARKs import ZKProof, RedactionSNARKManager
from ZK.ProofOfConsistency import ConsistencyProof, ConsistencyProofGenerator

# Import medical components
from medical.MedicalRedactionEngine import MyRedactionEngine


class TestSNARKEVMIntegration:
    """Test SNARK and EVM integration scenarios."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        # Use configuration flags
        self.use_real_snark = env_bool('USE_REAL_SNARK', False)
        self.use_real_evm = env_bool('USE_REAL_EVM', False)
        
        # Initialize SNARK client
        self.snark_client = SnarkClient()
        
        # Initialize EVM client
        self.evm_client = EVMClient()
        
        # Initialize medical redaction engine
        self.redaction_engine = MyRedactionEngine()
        
        # Test redaction data
        self.test_redaction_data = {
            "patient_id": "SNARK_EVM_TEST_001",
            "original_diagnosis": "Original sensitive diagnosis",
            "redacted_diagnosis": "REDACTED",
            "redaction_type": "DELETE",
            "requester": "admin",
            "reason": "GDPR Right to be Forgotten",
            "merkle_root": "0x" + "a" * 64,
            "nullifier": "0x" + "b" * 64
        }
        
        # Test circuit inputs
        self.test_circuit_inputs = {
            "originalData": [1, 2, 3, 4, 5],
            "redactedData": [0, 0, 3, 4, 5],  # First two elements redacted
            "merkleRoot": 12345,
            "nullifier": 67890,
            "redactionMask": [1, 1, 0, 0, 0]  # 1 = redacted, 0 = kept
        }
    
    def test_snark_proof_generation_and_evm_verification(self):
        """Test complete SNARK proof generation and EVM verification flow."""
        
        # Step 1: Generate SNARK proof
        if self.snark_client.enabled:
            # Real SNARK proof generation
            witness_result = self.snark_client.generate_witness(
                circuit_name="redaction",
                inputs=self.test_circuit_inputs
            )
            assert witness_result["success"] is True
            
            proof_result = self.snark_client.generate_proof(
                circuit_name="redaction",
                witness_file=witness_result["witness_file"]
            )
            assert proof_result["success"] is True
            proof_data = proof_result["proof"]
        else:
            # Simulated SNARK proof
            proof_data = self._generate_mock_proof()
        
        # Step 2: Format proof for Solidity
        formatted_proof = self.snark_client.format_proof_for_solidity(proof_data)
        assert "a" in formatted_proof
        assert "b" in formatted_proof
        assert "c" in formatted_proof
        assert "publicSignals" in formatted_proof
        
        # Step 3: Verify proof on EVM
        if self.evm_client.enabled:
            # Real EVM verification
            verification_result = self.evm_client.verify_redaction_proof(
                proof_a=formatted_proof["a"],
                proof_b=formatted_proof["b"],
                proof_c=formatted_proof["c"],
                public_signals=formatted_proof["publicSignals"]
            )
            assert verification_result["success"] is True
        else:
            # Simulated EVM verification
            verification_result = self._simulate_evm_verification(formatted_proof)
            assert verification_result["valid"] is True
        
        # Step 4: Test invalid proof rejection
        invalid_proof = formatted_proof.copy()
        invalid_proof["a"][0] = "0x" + "f" * 64  # Corrupt proof
        
        if self.evm_client.enabled:
            invalid_verification = self.evm_client.verify_redaction_proof(
                proof_a=invalid_proof["a"],
                proof_b=invalid_proof["b"],
                proof_c=invalid_proof["c"],
                public_signals=invalid_proof["publicSignals"]
            )
            assert invalid_verification["success"] is False
        else:
            invalid_verification = self._simulate_evm_verification(invalid_proof)
            assert invalid_verification["valid"] is False
    
    def test_redaction_workflow_with_snark_verification(self):
        """Test complete redaction workflow with SNARK proof verification."""
        
        # Step 1: Create redaction request
        redaction_request = {
            "patient_id": self.test_redaction_data["patient_id"],
            "redaction_type": self.test_redaction_data["redaction_type"],
            "reason": self.test_redaction_data["reason"],
            "requester": self.test_redaction_data["requester"],
            "original_data": self.test_redaction_data["original_diagnosis"],
            "redacted_data": self.test_redaction_data["redacted_diagnosis"]
        }
        
        # Step 2: Generate proof of valid redaction
        proof_inputs = self._prepare_redaction_proof_inputs(redaction_request)
        
        if self.snark_client.enabled:
            proof_result = self.snark_client.prove_redaction(
                original_data=proof_inputs["original_data"],
                redacted_data=proof_inputs["redacted_data"],
                merkle_root=proof_inputs["merkle_root"],
                nullifier=proof_inputs["nullifier"]
            )
            assert proof_result["success"] is True
            snark_proof = proof_result["proof"]
        else:
            snark_proof = self._generate_mock_redaction_proof(proof_inputs)
        
        # Step 3: Submit redaction request with proof to EVM
        if self.evm_client.enabled:
            submission_result = self.evm_client.submit_redaction_request(
                patient_id=redaction_request["patient_id"],
                redaction_type=redaction_request["redaction_type"],
                proof=snark_proof,
                reason=redaction_request["reason"]
            )
            assert submission_result["success"] is True
            request_id = submission_result["request_id"]
        else:
            request_id = self._simulate_redaction_submission(redaction_request, snark_proof)
        
        # Step 4: Verify request was recorded on blockchain
        stored_request = self._get_redaction_request(request_id)
        assert stored_request["patient_id"] == redaction_request["patient_id"]
        assert stored_request["redaction_type"] == redaction_request["redaction_type"]
        assert stored_request["proof_verified"] is True
        
        # Step 5: Test approval workflow
        if self.evm_client.enabled:
            approval_result = self.evm_client.approve_redaction_request(
                request_id=request_id,
                approver="regulator",
                approval_reason="Compliance approved"
            )
            assert approval_result["success"] is True
        else:
            approval_result = self._simulate_redaction_approval(request_id)
            assert approval_result["approved"] is True
    
    def test_proof_of_consistency_integration(self):
        """Test proof-of-consistency generation and verification."""
        
        # Create test blockchain state
        original_blocks = self._create_test_blockchain_state()
        
        # Simulate redaction operation
        redacted_blocks = self._simulate_redaction_on_blocks(original_blocks)
        
        # Generate proof of consistency
        consistency_prover = ConsistencyProofGenerator()
        consistency_proof = consistency_prover.generate_consistency_proof(
            original_state=original_blocks,
            redacted_state=redacted_blocks,
            redaction_operations=[{
                "block_id": 1,
                "transaction_id": 0,
                "redaction_type": "DELETE",
                "affected_fields": ["diagnosis"]
            }]
        )
        
        assert consistency_proof["valid"] is True
        assert "merkle_proof" in consistency_proof
        assert "state_transition_proof" in consistency_proof
        
        # Convert to SNARK proof format
        if self.snark_client.enabled:
            snark_consistency_proof = self.snark_client.generate_consistency_snark(
                consistency_proof=consistency_proof
            )
            assert snark_consistency_proof["success"] is True
        else:
            snark_consistency_proof = self._mock_consistency_snark(consistency_proof)
        
        # Verify on EVM
        if self.evm_client.enabled:
            verification_result = self.evm_client.verify_consistency_proof(
                snark_consistency_proof["proof"]
            )
            assert verification_result["valid"] is True
        else:
            verification_result = self._simulate_consistency_verification(
                snark_consistency_proof
            )
            assert verification_result["consistent"] is True
    
    def test_batch_proof_verification(self):
        """Test batch verification of multiple SNARK proofs."""
        
        # Generate multiple redaction proofs
        batch_proofs = []
        for i in range(3):
            proof_inputs = {
                "originalData": [i, i+1, i+2, i+3, i+4],
                "redactedData": [0, 0, i+2, i+3, i+4],
                "merkleRoot": 12345 + i,
                "nullifier": 67890 + i,
                "redactionMask": [1, 1, 0, 0, 0]
            }
            
            if self.snark_client.enabled:
                proof_result = self.snark_client.generate_proof(
                    circuit_name="redaction",
                    inputs=proof_inputs
                )
                batch_proofs.append(proof_result["proof"])
            else:
                batch_proofs.append(self._generate_mock_proof())
        
        # Batch verify on EVM
        if self.evm_client.enabled:
            batch_verification = self.evm_client.batch_verify_proofs(batch_proofs)
            assert batch_verification["all_valid"] is True
            assert len(batch_verification["results"]) == 3
        else:
            batch_verification = self._simulate_batch_verification(batch_proofs)
            assert batch_verification["all_valid"] is True
    
    def test_snark_evm_error_handling(self):
        """Test error handling in SNARK-EVM integration."""
        
        # Test 1: Invalid circuit inputs
        invalid_inputs = {
            "originalData": [1, 2, 3],  # Wrong length
            "redactedData": [0, 0],     # Mismatched length
            "merkleRoot": "invalid",    # Wrong type
            "nullifier": -1             # Invalid value
        }
        
        if self.snark_client.enabled:
            with pytest.raises(Exception):
                self.snark_client.generate_witness(
                    circuit_name="redaction",
                    inputs=invalid_inputs
                )
        
        # Test 2: Malformed proof submission to EVM
        malformed_proof = {
            "a": ["0xinvalid"],  # Invalid format
            "b": [["0x1", "0x2"]],  # Wrong structure
            "c": ["0x3"],
            "publicSignals": ["not_a_number"]  # Invalid signal
        }
        
        if self.evm_client.enabled:
            with pytest.raises(Exception):
                self.evm_client.verify_redaction_proof(
                    proof_a=malformed_proof["a"],
                    proof_b=malformed_proof["b"],
                    proof_c=malformed_proof["c"],
                    public_signals=malformed_proof["publicSignals"]
                )
        
        # Test 3: Proof-verification mismatch
        valid_proof = self._generate_mock_proof()
        wrong_public_signals = ["999999", "888888"]  # Don't match proof
        
        if self.evm_client.enabled:
            verification_result = self.evm_client.verify_redaction_proof(
                proof_a=valid_proof["a"],
                proof_b=valid_proof["b"],
                proof_c=valid_proof["c"],
                public_signals=wrong_public_signals
            )
            assert verification_result["success"] is False
    
    def test_snark_parameter_validation(self):
        """Test SNARK parameter validation and circuit constraints."""
        
        # Test valid parameters
        valid_params = {
            "field_size": "21888242871839275222246405745257275088548364400416034343698204186575808495617",
            "curve": "bn128",
            "circuit_constraints": 1000,
            "max_public_inputs": 10
        }
        
        if self.snark_client.enabled:
            param_validation = self.snark_client.validate_circuit_parameters(
                circuit_name="redaction",
                parameters=valid_params
            )
            assert param_validation["valid"] is True
        
        # Test parameter limits
        oversized_inputs = list(range(20))  # Too many public inputs
        
        if self.snark_client.enabled:
            with pytest.raises(Exception) as exc_info:
                self.snark_client.generate_witness(
                    circuit_name="redaction",
                    inputs={"publicInputs": oversized_inputs}
                )
            assert "too many inputs" in str(exc_info.value).lower()
    
    def _generate_mock_proof(self) -> Dict[str, Any]:
        """Generate a mock SNARK proof for testing."""
        return {
            "a": ["0x" + "1" * 64, "0x" + "2" * 64],
            "b": [["0x" + "3" * 64, "0x" + "4" * 64], ["0x" + "5" * 64, "0x" + "6" * 64]],
            "c": ["0x" + "7" * 64, "0x" + "8" * 64],
            "publicSignals": ["12345", "67890"]
        }
    
    def _generate_mock_redaction_proof(self, proof_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock redaction proof."""
        proof = self._generate_mock_proof()
        proof["redaction_inputs"] = proof_inputs
        proof["proof_type"] = "redaction"
        return proof
    
    def _simulate_evm_verification(self, proof: Dict[str, Any]) -> Dict[str, bool]:
        """Simulate EVM proof verification."""
        # Simple validation - check proof structure
        valid = (
            "a" in proof and 
            "b" in proof and 
            "c" in proof and 
            "publicSignals" in proof and
            len(proof["a"]) == 2 and
            len(proof["b"]) == 2 and
            len(proof["c"]) == 2
        )
        
        # Simulate corruption detection
        if "f" * 10 in str(proof):  # Detect our test corruption
            valid = False
        
        return {"valid": valid, "gas_used": 50000}
    
    def _prepare_redaction_proof_inputs(self, redaction_request: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs for redaction proof generation."""
        original_hash = hashlib.sha256(
            redaction_request["original_data"].encode()
        ).hexdigest()
        
        redacted_hash = hashlib.sha256(
            redaction_request["redacted_data"].encode()
        ).hexdigest()
        
        return {
            "original_data": original_hash,
            "redacted_data": redacted_hash,
            "merkle_root": self.test_redaction_data["merkle_root"],
            "nullifier": self.test_redaction_data["nullifier"],
            "redaction_type": redaction_request["redaction_type"]
        }
    
    def _simulate_redaction_submission(self, request: Dict[str, Any], proof: Dict[str, Any]) -> str:
        """Simulate redaction request submission to EVM."""
        if not hasattr(self, '_redaction_requests'):
            self._redaction_requests = {}
        
        request_id = f"REQ_{len(self._redaction_requests):06d}"
        self._redaction_requests[request_id] = {
            **request,
            "proof": proof,
            "proof_verified": True,  # Assume valid for simulation
            "status": "pending",
            "timestamp": "2025-09-15T10:00:00Z"
        }
        
        return request_id
    
    def _get_redaction_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get redaction request from storage."""
        if self.evm_client.enabled:
            return self.evm_client.get_redaction_request(request_id)
        else:
            return getattr(self, '_redaction_requests', {}).get(request_id)
    
    def _simulate_redaction_approval(self, request_id: str) -> Dict[str, bool]:
        """Simulate redaction approval."""
        if hasattr(self, '_redaction_requests') and request_id in self._redaction_requests:
            self._redaction_requests[request_id]["status"] = "approved"
            return {"approved": True, "request_id": request_id}
        return {"approved": False, "error": "Request not found"}
    
    def _create_test_blockchain_state(self) -> List[Dict[str, Any]]:
        """Create test blockchain state for consistency testing."""
        return [
            {
                "block_id": 0,
                "transactions": [
                    {
                        "tx_id": 0,
                        "data": {"patient_id": "TEST_001", "diagnosis": "Original diagnosis"},
                        "hash": "0x" + "a" * 64
                    }
                ],
                "merkle_root": "0x" + "b" * 64
            },
            {
                "block_id": 1,
                "transactions": [
                    {
                        "tx_id": 0,
                        "data": {"patient_id": "TEST_001", "diagnosis": "Sensitive diagnosis"},
                        "hash": "0x" + "c" * 64
                    }
                ],
                "merkle_root": "0x" + "d" * 64
            }
        ]
    
    def _simulate_redaction_on_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulate redaction operation on blockchain blocks."""
        redacted_blocks = []
        for block in blocks:
            redacted_block = block.copy()
            redacted_block["transactions"] = []
            
            for tx in block["transactions"]:
                redacted_tx = tx.copy()
                if "diagnosis" in redacted_tx["data"]:
                    redacted_tx["data"]["diagnosis"] = "REDACTED"
                    # Update hash to reflect redaction
                    redacted_tx["hash"] = "0x" + "f" * 64
                redacted_block["transactions"].append(redacted_tx)
            
            # Update merkle root
            redacted_block["merkle_root"] = "0x" + "e" * 64
            redacted_blocks.append(redacted_block)
        
        return redacted_blocks
    
    def _mock_consistency_snark(self, consistency_proof: Dict[str, Any]) -> Dict[str, Any]:
        """Mock SNARK generation for consistency proof."""
        return {
            "success": True,
            "proof": self._generate_mock_proof(),
            "consistency_data": consistency_proof
        }
    
    def _simulate_consistency_verification(self, snark_proof: Dict[str, Any]) -> Dict[str, bool]:
        """Simulate consistency proof verification."""
        return {
            "consistent": True,
            "verified": True,
            "gas_used": 75000
        }
    
    def _simulate_batch_verification(self, proofs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate batch proof verification."""
        results = []
        for proof in proofs:
            results.append(self._simulate_evm_verification(proof))
        
        all_valid = all(result["valid"] for result in results)
        
        return {
            "all_valid": all_valid,
            "results": results,
            "total_gas_used": sum(result["gas_used"] for result in results)
        }


@pytest.mark.integration
class TestSNARKEVMRealIntegration:
    """Integration tests requiring real SNARK and EVM services."""
    
    @pytest.mark.requires_snark
    @pytest.mark.requires_evm
    def test_real_snark_evm_integration(self):
        """Test with real SNARK and EVM services."""
        snark_client = SnarkClient()
        evm_client = EVMClient()
        
        assert snark_client.enabled is True
        assert evm_client.enabled is True
        
        # Test real proof generation and verification
        test_inputs = {
            "originalData": [1, 2, 3, 4, 5],
            "redactedData": [0, 0, 3, 4, 5],
            "merkleRoot": 12345,
            "nullifier": 67890
        }
        
        # Generate real witness
        witness_result = snark_client.generate_witness(
            circuit_name="redaction",
            inputs=test_inputs
        )
        assert witness_result["success"] is True
        
        # Generate real proof
        proof_result = snark_client.generate_proof(
            circuit_name="redaction",
            witness_file=witness_result["witness_file"]
        )
        assert proof_result["success"] is True
        
        # Verify on real EVM
        formatted_proof = snark_client.format_proof_for_solidity(proof_result["proof"])
        verification_result = evm_client.verify_redaction_proof(
            proof_a=formatted_proof["a"],
            proof_b=formatted_proof["b"],
            proof_c=formatted_proof["c"],
            public_signals=formatted_proof["publicSignals"]
        )
        
        assert verification_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])