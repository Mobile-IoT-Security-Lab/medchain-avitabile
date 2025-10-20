"""
Integration tests for consistency proof wired into ZK circuit.

Tests the complete flow:
1. Generate consistency proof (ConsistencyProofGenerator)
2. Map to circuit inputs with consistency (MedicalDataCircuitMapper)
3. Generate SNARK proof with consistency (EnhancedHybridSNARKManager)
4. Verify the proof includes consistency verification

### Bookmark1 for next meeting
"""
import pytest
import json
import hashlib
from typing import Dict, Any

# Import consistency proof components
from ZK.ProofOfConsistency import (
    ConsistencyProofGenerator,
    ConsistencyProof,
    ConsistencyCheckType,
    MerkleTreeConsistency,
    HashChainConsistency,
    SmartContractStateConsistency
)

# Import circuit mapper and SNARK manager
from medical.circuit_mapper import MedicalDataCircuitMapper, CircuitInputs
from medical.my_snark_manager import EnhancedHybridSNARKManager

# Import SNARK client
from adapters.snark import SnarkClient


class TestConsistencyCircuitIntegration:
    """Test suite for consistency proof integration into ZK circuit."""
    
    @pytest.fixture
    def sample_medical_record(self):
        """Sample medical record for testing."""
        return {
            "patient_id": "P12345",
            "age": "45",
            "diagnosis": "Type 2 Diabetes",
            "medication": "Metformin 500mg",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    @pytest.fixture
    def redacted_medical_record(self):
        """Redacted version of medical record."""
        return {
            "patient_id": "P12345",
            "age": "45",
            "diagnosis": "[REDACTED]",
            "medication": "[REDACTED]",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    @pytest.fixture
    def circuit_mapper(self):
        """Circuit mapper instance."""
        return MedicalDataCircuitMapper()
    
    @pytest.fixture
    def snark_manager(self):
        """SNARK manager instance."""
        return EnhancedHybridSNARKManager()
    
    @pytest.fixture
    def consistency_proof_generator(self):
        """Consistency proof generator with Merkle and hash chain."""
        return ConsistencyProofGenerator()
    
    def test_hash_state_method(self, circuit_mapper):
        """Test the _hash_state helper method."""
        state1 = {"a": 1, "b": 2, "c": 3}
        state2 = {"c": 3, "a": 1, "b": 2}  # Different order
        state3 = {"a": 1, "b": 2, "c": 4}  # Different value
        
        hash1 = circuit_mapper._hash_state(state1)
        hash2 = circuit_mapper._hash_state(state2)
        hash3 = circuit_mapper._hash_state(state3)
        
        # Same content = same hash (canonical JSON)
        assert hash1 == hash2
        # Different content = different hash
        assert hash1 != hash3
        # Hash is hex string (64 chars for SHA256)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)
    
    def test_prepare_circuit_inputs_with_consistency_no_proof(self, circuit_mapper, sample_medical_record):
        """Test circuit input preparation when no consistency proof provided."""
        circuit_inputs = circuit_mapper.prepare_circuit_inputs_with_consistency(
            medical_record_dict=sample_medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_MODIFY",
            consistency_proof=None  # No proof
        )
        
        # Should have all base fields
        assert hasattr(circuit_inputs, 'public_inputs')
        assert hasattr(circuit_inputs, 'private_inputs')
        
        # Consistency fields should be zero (no proof)
        assert circuit_inputs.public_inputs['preStateHash0'] == 0
        assert circuit_inputs.public_inputs['preStateHash1'] == 0
        assert circuit_inputs.public_inputs['postStateHash0'] == 0
        assert circuit_inputs.public_inputs['postStateHash1'] == 0
        assert circuit_inputs.public_inputs['consistencyCheckPassed'] == 0
    
    def test_prepare_circuit_inputs_with_consistency_valid_proof(
        self, 
        circuit_mapper, 
        sample_medical_record,
        consistency_proof_generator
    ):
        """Test circuit input preparation with valid consistency proof."""
        # Create pre/post states
        pre_state = {"record": sample_medical_record, "version": 1}
        post_state = {"record": sample_medical_record, "version": 2}
        
        # Generate consistency proof using correct API
        consistency_proof = consistency_proof_generator.generate_consistency_proof(
            check_type=ConsistencyCheckType.HASH_CHAIN,
            pre_redaction_data=pre_state,
            post_redaction_data=post_state,
            operation_details={"operation": "redaction"}
        )
        
        # Prepare circuit inputs WITH consistency proof
        circuit_inputs = circuit_mapper.prepare_circuit_inputs_with_consistency(
            medical_record_dict=sample_medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_MODIFY",
            consistency_proof=consistency_proof
        )
        
        # Should have all fields
        assert hasattr(circuit_inputs, 'public_inputs')
        assert hasattr(circuit_inputs, 'private_inputs')
        
        # Consistency fields should be non-zero
        assert circuit_inputs.public_inputs['preStateHash0'] != 0
        assert circuit_inputs.public_inputs['preStateHash1'] != 0
        assert circuit_inputs.public_inputs['postStateHash0'] != 0
        assert circuit_inputs.public_inputs['postStateHash1'] != 0
        
        # Should pass consistency check (valid proof)
        assert circuit_inputs.public_inputs['consistencyCheckPassed'] == 1
    
    def test_prepare_circuit_inputs_with_consistency_invalid_proof(
        self, 
        circuit_mapper, 
        sample_medical_record,
        consistency_proof_generator
    ):
        """Test circuit input preparation with invalid consistency proof."""
        # Create pre/post states
        pre_state = {"record": sample_medical_record, "version": 1}
        post_state = {"record": sample_medical_record, "version": 2}
        
        # Generate consistency proof using correct API
        consistency_proof = consistency_proof_generator.generate_consistency_proof(
            check_type=ConsistencyCheckType.HASH_CHAIN,
            pre_redaction_data=pre_state,
            post_redaction_data=post_state,
            operation_details={"operation": "redaction"}
        )
        
        # Manually invalidate proof
        consistency_proof.is_valid = False
        
        # Prepare circuit inputs WITH invalid consistency proof
        circuit_inputs = circuit_mapper.prepare_circuit_inputs_with_consistency(
            medical_record_dict=sample_medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_MODIFY",
            consistency_proof=consistency_proof
        )
        
        # State hashes should still be computed
        assert circuit_inputs.public_inputs['preStateHash0'] != 0
        assert circuit_inputs.public_inputs['preStateHash1'] != 0
        assert circuit_inputs.public_inputs['postStateHash0'] != 0
        assert circuit_inputs.public_inputs['postStateHash1'] != 0
        
        # Should FAIL consistency check (invalid proof)
        assert circuit_inputs.public_inputs['consistencyCheckPassed'] == 0
    
    def test_validate_circuit_inputs_with_consistency_valid(
        self, 
        circuit_mapper, 
        sample_medical_record,
        consistency_proof_generator
    ):
        """Test validation of circuit inputs with consistency fields."""
        # Create consistency proof
        pre_state = {"record": sample_medical_record, "version": 1}
        post_state = {"record": sample_medical_record, "version": 2}
        consistency_proof = consistency_proof_generator.generate_consistency_proof(
            check_type=ConsistencyCheckType.HASH_CHAIN,
            pre_redaction_data=pre_state,
            post_redaction_data=post_state,
            operation_details={"operation": "redaction"}
        )
        
        # Prepare valid inputs
        circuit_inputs = circuit_mapper.prepare_circuit_inputs_with_consistency(
            medical_record_dict=sample_medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_MODIFY",
            consistency_proof=consistency_proof
        )
        
        # Should validate successfully
        assert circuit_mapper.validate_circuit_inputs_with_consistency(circuit_inputs)
    
    def test_validate_circuit_inputs_with_consistency_missing_fields(
        self, 
        circuit_mapper, 
        sample_medical_record
    ):
        """Test validation fails when consistency fields missing."""
        # Prepare inputs WITHOUT consistency (uses base method)
        circuit_inputs = circuit_mapper.prepare_circuit_inputs(
            medical_record_dict=sample_medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_MODIFY"
        )
        
        # Should fail validation (missing consistency fields)
        assert not circuit_mapper.validate_circuit_inputs_with_consistency(circuit_inputs)
    
    def test_snark_manager_with_consistency_proof(
        self, 
        snark_manager,
        sample_medical_record,
        redacted_medical_record,
        consistency_proof_generator
    ):
        """Test SNARK manager generates proof with consistency verification."""
        from shutil import which
        if which("snarkjs") is None:
            pytest.skip("snarkjs CLI not available; real proof generation required")
        # Create redaction data (with all required fields for simulation fallback)
        redaction_data = {
            "request_id": "req_123",
            "transaction_id": "tx_123",
            "redaction_type": "MODIFY",
            "policy_hash": "policy_MODIFY",
            "original_data": json.dumps(sample_medical_record),
            "redacted_data": json.dumps(redacted_medical_record),
            "timestamp": 1234567890,
            # Required for simulation fallback
            "target_block": 1,
            "target_tx": "tx_123",
            "requester": "doctor_123",
            "requester_role": "DOCTOR"
        }
        
        # Create consistency proof
        pre_state = {"record": sample_medical_record, "version": 1}
        post_state = {"record": redacted_medical_record, "version": 2}
        consistency_proof = consistency_proof_generator.generate_consistency_proof(
            check_type=ConsistencyCheckType.HASH_CHAIN,
            pre_redaction_data=pre_state,
            post_redaction_data=post_state,
            operation_details={"operation": "redaction"}
        )
        
        # Generate SNARK proof WITH consistency
        zk_proof = snark_manager.create_redaction_proof_with_consistency(
            redaction_data=redaction_data,
            consistency_proof=consistency_proof
        )
        
        # Should generate proof when real snarkjs tooling is available
        assert zk_proof is not None
        assert zk_proof.proof_id is not None
        assert zk_proof.operation_type == "MODIFY"
    
    def test_snark_manager_without_consistency_proof(
        self, 
        snark_manager,
        sample_medical_record,
        redacted_medical_record
    ):
        """Test SNARK manager when no consistency proof provided."""
        from shutil import which
        if which("snarkjs") is None:
            pytest.skip("snarkjs CLI not available; real proof generation required")
        # Create redaction data (with all required fields for simulation fallback)
        redaction_data = {
            "request_id": "req_124",
            "transaction_id": "tx_124",
            "redaction_type": "DELETE",
            "policy_hash": "policy_DELETE",
            "original_data": json.dumps(sample_medical_record),
            "redacted_data": json.dumps(redacted_medical_record),
            "timestamp": 1234567891,
            # Required for simulation fallback
            "target_block": 2,
            "target_tx": "tx_124",
            "requester": "admin_456",
            "requester_role": "ADMIN"
        }
        
        # Generate SNARK proof WITHOUT consistency (None)
        zk_proof = snark_manager.create_redaction_proof_with_consistency(
            redaction_data=redaction_data,
            consistency_proof=None
        )
        
        # Should still generate proof
        assert zk_proof is not None
        assert zk_proof.proof_id is not None
        assert zk_proof.operation_type == "DELETE"
        
        # If real mode, consistency fields should be zero
        if snark_manager.use_real and snark_manager.snark_client and snark_manager.snark_client.is_available():
            prover_response = json.loads(zk_proof.prover_response)
            if len(prover_response) >= 13:
                # Consistency fields should be zero
                assert int(prover_response[8]) == 0   # preStateHash0
                assert int(prover_response[9]) == 0   # preStateHash1
                assert int(prover_response[10]) == 0  # postStateHash0
                assert int(prover_response[11]) == 0  # postStateHash1
                assert int(prover_response[12]) == 0  # consistencyCheckPassed
    
    def test_end_to_end_consistency_integration(
        self,
        circuit_mapper,
        snark_manager,
        consistency_proof_generator,
        sample_medical_record,
        redacted_medical_record
    ):
        """Test complete end-to-end flow with consistency proof integration."""
        from shutil import which
        if which("snarkjs") is None:
            pytest.skip("snarkjs CLI not available; real proof generation required")
        print("\n=== End-to-End Consistency Circuit Integration Test ===")
        
        # Step 1: Create pre/post states
        print("\n1. Creating pre/post states...")
        pre_state = {
            "patient_id": sample_medical_record["patient_id"],
            "diagnosis": sample_medical_record["diagnosis"],
            "medication": sample_medical_record["medication"],
            "version": 1
        }
        post_state = {
            "patient_id": redacted_medical_record["patient_id"],
            "diagnosis": redacted_medical_record["diagnosis"],
            "medication": redacted_medical_record["medication"],
            "version": 2
        }
        print(f"   Pre-state: {pre_state}")
        print(f"   Post-state: {post_state}")
        
        # Step 2: Generate consistency proof
        print("\n2. Generating consistency proof...")
        consistency_proof = consistency_proof_generator.generate_consistency_proof(
            check_type=ConsistencyCheckType.HASH_CHAIN,
            pre_redaction_data=pre_state,
            post_redaction_data=post_state,
            operation_details={"operation": "medical_redaction"}
        )
        print(f"   Proof valid: {consistency_proof.is_valid}")
        print(f"   Check type: {consistency_proof.check_type.value}")
        
        # Step 3: Prepare circuit inputs with consistency
        print("\n3. Preparing circuit inputs with consistency...")
        circuit_inputs = circuit_mapper.prepare_circuit_inputs_with_consistency(
            medical_record_dict=sample_medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_medical_redaction",
            consistency_proof=consistency_proof
        )
        print(f"   Public inputs: {len(circuit_inputs.public_inputs)} fields")
        print(f"   Consistency check passed: {circuit_inputs.public_inputs['consistencyCheckPassed']}")
        
        # Step 4: Validate inputs
        print("\n4. Validating circuit inputs...")
        is_valid = circuit_mapper.validate_circuit_inputs_with_consistency(circuit_inputs)
        print(f"   Validation: {'PASS' if is_valid else 'FAIL'}")
        assert is_valid
        
        # Step 5: Generate SNARK proof with consistency
        print("\n5. Generating SNARK proof with consistency...")
        redaction_data = {
            "request_id": "req_e2e_001",
            "transaction_id": "tx_e2e_001",
            "redaction_type": "MODIFY",
            "policy_hash": "policy_medical_redaction",
            "original_data": json.dumps(sample_medical_record),
            "redacted_data": json.dumps(redacted_medical_record),
            "timestamp": 1234567892,
            # Required for simulation fallback
            "target_block": 3,
            "target_tx": "tx_e2e_001",
            "requester": "doctor_789",
            "requester_role": "DOCTOR"
        }
        zk_proof = snark_manager.create_redaction_proof_with_consistency(
            redaction_data=redaction_data,
            consistency_proof=consistency_proof
        )
        
        print(f"   Proof generated: {zk_proof is not None}")
        print(f"   Proof ID: {zk_proof.proof_id if zk_proof else 'None'}")
        print(f"   Operation: {zk_proof.operation_type if zk_proof else 'None'}")
        
        # Verify proof was created
        assert zk_proof is not None
        assert zk_proof.proof_id is not None
        assert zk_proof.operation_type == "MODIFY"
        
        print("\n=== End-to-End Test PASSED ===")


class TestConsistencyCircuitEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def circuit_mapper(self):
        return MedicalDataCircuitMapper()
    
    def test_empty_state_hashing(self, circuit_mapper):
        """Test hashing of empty state."""
        empty_state = {}
        hash_result = circuit_mapper._hash_state(empty_state)
        assert hash_result is not None
        assert len(hash_result) == 64
        
        # Empty state should be deterministic
        hash_result2 = circuit_mapper._hash_state({})
        assert hash_result == hash_result2
    
    def test_large_state_hashing(self, circuit_mapper):
        """Test hashing of large state dictionary."""
        large_state = {f"key_{i}": f"value_{i}" for i in range(1000)}
        hash_result = circuit_mapper._hash_state(large_state)
        assert hash_result is not None
        assert len(hash_result) == 64
    
    def test_nested_state_hashing(self, circuit_mapper):
        """Test hashing of nested state structures."""
        nested_state = {
            "patient": {
                "id": "P123",
                "records": [
                    {"date": "2024-01-01", "diagnosis": "Flu"},
                    {"date": "2024-01-15", "diagnosis": "Diabetes"}
                ]
            },
            "metadata": {
                "version": 1,
                "timestamp": 1234567890
            }
        }
        hash_result = circuit_mapper._hash_state(nested_state)
        assert hash_result is not None
        assert len(hash_result) == 64
    
    def test_consistency_with_special_characters(self, circuit_mapper):
        """Test consistency proof with special characters in data."""
        medical_record = {
            "patient_id": "P12345",
            "diagnosis": "Type 2 Diabetes & Hypertension",
            "notes": "Patient reports symptoms: \"chest pain\", 'dizziness'"
        }
        
        circuit_inputs = circuit_mapper.prepare_circuit_inputs_with_consistency(
            medical_record_dict=medical_record,
            redaction_type="MODIFY",
            policy_hash="policy_test",
            consistency_proof=None
        )
        
        assert circuit_inputs is not None
        assert circuit_mapper.validate_circuit_inputs_with_consistency(circuit_inputs)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
