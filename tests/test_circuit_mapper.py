"""
Tests for Medical Data Circuit Mapper
=====================================

Tests the mapping of medical data to circom circuit inputs.

### Bookmark1 for next meeting
"""

import pytest
import json
from medical.circuit_mapper import MedicalDataCircuitMapper, CircuitInputs


class TestMedicalDataCircuitMapper:
    """Test suite for circuit input mapping."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mapper = MedicalDataCircuitMapper()
        self.sample_record = {
            "patient_id": "TEST_PAT_001",
            "patient_name": "Test Patient",
            "diagnosis": "Test Diagnosis",
            "treatment": "Test Treatment",
            "physician": "Dr. Test"
        }
    
    def test_hash_to_field_elements(self):
        """Test conversion of hash to field elements."""
        data = "test data"
        elements = self.mapper.hash_to_field_elements(data, 4)
        
        assert len(elements) == 4
        assert all(isinstance(e, int) for e in elements)
        assert all(e >= 0 for e in elements)
        # Check elements are within reasonable field bounds
        assert all(e < 2**250 for e in elements)
    
    def test_split_256bit_hash(self):
        """Test splitting 256-bit hash into limbs."""
        # Test with hex string (no prefix)
        hash_hex = "a" * 64  # 256-bit hash
        limb0, limb1 = self.mapper.split_256bit_hash(hash_hex)
        
        assert isinstance(limb0, int)
        assert isinstance(limb1, int)
        assert limb0 < 2**128
        assert limb1 < 2**128
        
        # Test with 0x prefix
        hash_hex_prefixed = "0x" + "b" * 64
        limb0_p, limb1_p = self.mapper.split_256bit_hash(hash_hex_prefixed)
        assert isinstance(limb0_p, int)
        assert isinstance(limb1_p, int)
    
    def test_serialize_medical_data(self):
        """Test canonical serialization of medical data."""
        serialized = self.mapper.serialize_medical_data(self.sample_record)
        
        # Should be valid JSON
        data = json.loads(serialized)
        assert isinstance(data, dict)
        
        # Should contain key fields
        assert "patient_id" in data
        assert "diagnosis" in data
        assert "treatment" in data
        assert "physician" in data
        
        # Should be deterministic (same record -> same serialization)
        serialized2 = self.mapper.serialize_medical_data(self.sample_record)
        assert serialized == serialized2
    
    def test_apply_redaction_delete(self):
        """Test DELETE redaction."""
        original = self.mapper.serialize_medical_data(self.sample_record)
        redacted = self.mapper.apply_redaction(original, "DELETE")
        
        data = json.loads(redacted)
        assert data == {}
    
    def test_apply_redaction_anonymize(self):
        """Test ANONYMIZE redaction."""
        original = self.mapper.serialize_medical_data(self.sample_record)
        redacted = self.mapper.apply_redaction(original, "ANONYMIZE")
        
        data = json.loads(redacted)
        # Patient ID should be preserved for tracking
        assert data["patient_id"] == "TEST_PAT_001"
        # Other fields should be redacted
        assert data["diagnosis"] == "[REDACTED]"
        assert data["treatment"] == "[REDACTED]"
        assert data["physician"] == "[REDACTED]"
    
    def test_apply_redaction_modify(self):
        """Test MODIFY redaction."""
        original = self.mapper.serialize_medical_data(self.sample_record)
        redacted = self.mapper.apply_redaction(original, "MODIFY")
        
        data = json.loads(redacted)
        # Patient ID should be preserved
        assert data["patient_id"] == "TEST_PAT_001"
        # Sensitive fields should be modified
        assert data["diagnosis"] == "[MODIFIED]"
        assert data["treatment"] == "[MODIFIED]"
    
    def test_prepare_circuit_inputs_structure(self):
        """Test circuit inputs preparation structure."""
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "ANONYMIZE"
        )
        
        assert isinstance(inputs, CircuitInputs)
        assert isinstance(inputs.public_inputs, dict)
        assert isinstance(inputs.private_inputs, dict)
    
    def test_prepare_circuit_inputs_public(self):
        """Test public inputs are correctly prepared."""
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "DELETE"
        )
        
        public = inputs.public_inputs
        
        # Check all required keys present
        required_keys = [
            "policyHash0", "policyHash1",
            "merkleRoot0", "merkleRoot1",
            "originalHash0", "originalHash1",
            "redactedHash0", "redactedHash1",
            "policyAllowed"
        ]
        
        for key in required_keys:
            assert key in public, f"Missing public input: {key}"
            assert isinstance(public[key], int), f"{key} should be int"
    
    def test_prepare_circuit_inputs_private(self):
        """Test private inputs are correctly prepared."""
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "MODIFY"
        )
        
        private = inputs.private_inputs
        
        # Check array lengths
        assert len(private["originalData"]) == 4
        assert len(private["redactedData"]) == 4
        assert len(private["policyData"]) == 2
        assert len(private["merklePathElements"]) == 8
        assert len(private["merklePathIndices"]) == 8
        
        # Check types
        assert all(isinstance(x, int) for x in private["originalData"])
        assert all(isinstance(x, int) for x in private["redactedData"])
        assert all(isinstance(x, int) for x in private["policyData"])
    
    def test_validate_circuit_inputs_valid(self):
        """Test validation passes for valid inputs."""
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "ANONYMIZE"
        )
        
        assert self.mapper.validate_circuit_inputs(inputs)
    
    def test_validate_circuit_inputs_missing_public(self):
        """Test validation fails for missing public input."""
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "DELETE"
        )
        
        # Remove a public input
        del inputs.public_inputs["policyHash0"]
        
        assert not self.mapper.validate_circuit_inputs(inputs)
    
    def test_validate_circuit_inputs_wrong_array_size(self):
        """Test validation fails for wrong array size."""
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "MODIFY"
        )
        
        # Change array size
        inputs.private_inputs["originalData"] = [1, 2, 3]  # Should be 4
        
        assert not self.mapper.validate_circuit_inputs(inputs)
    
    def test_different_redaction_types_produce_different_hashes(self):
        """Test that different redaction types produce different hashes."""
        inputs_delete = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "DELETE"
        )
        inputs_anonymize = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "ANONYMIZE"
        )
        
        # Redacted hashes should be different
        assert inputs_delete.public_inputs["redactedHash0"] != \
               inputs_anonymize.public_inputs["redactedHash0"]
    
    def test_deterministic_mapping(self):
        """Test that mapping is deterministic."""
        inputs1 = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "ANONYMIZE"
        )
        inputs2 = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "ANONYMIZE"
        )
        
        # Should produce identical outputs
        assert inputs1.public_inputs == inputs2.public_inputs
        assert inputs1.private_inputs == inputs2.private_inputs
    
    def test_custom_policy_hash(self):
        """Test using custom policy hash."""
        custom_policy = "custom_gdpr_policy_v1"
        
        inputs = self.mapper.prepare_circuit_inputs(
            self.sample_record,
            "DELETE",
            policy_hash=custom_policy
        )
        
        # Should have non-zero policy hash
        assert inputs.public_inputs["policyHash0"] > 0 or \
               inputs.public_inputs["policyHash1"] > 0
    
    def test_empty_record_handling(self):
        """Test handling of empty/minimal records."""
        minimal_record = {"patient_id": "MIN_001"}
        
        inputs = self.mapper.prepare_circuit_inputs(
            minimal_record,
            "ANONYMIZE"
        )
        
        # Should still produce valid inputs
        assert self.mapper.validate_circuit_inputs(inputs)
    
    def test_field_element_range(self):
        """Test that field elements stay within acceptable range."""
        # Use record with very long strings
        large_record = {
            "patient_id": "LARGE_" + "X" * 1000,
            "diagnosis": "Y" * 1000,
            "treatment": "Z" * 1000,
            "physician": "W" * 1000
        }
        
        inputs = self.mapper.prepare_circuit_inputs(
            large_record,
            "DELETE"
        )
        
        # All field elements should be within bounds
        for elem in inputs.private_inputs["originalData"]:
            assert elem < 2**250  # Well below BN254 field prime
        
        for elem in inputs.private_inputs["redactedData"]:
            assert elem < 2**250


class TestCircuitInputsIntegration:
    """Integration tests for circuit inputs with redaction workflow."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mapper = MedicalDataCircuitMapper()
    
    def test_full_redaction_workflow_delete(self):
        """Test complete DELETE workflow."""
        record = {
            "patient_id": "WORKFLOW_001",
            "diagnosis": "Sensitive diagnosis",
            "treatment": "Sensitive treatment",
            "physician": "Dr. Secret"
        }
        
        # Prepare inputs
        inputs = self.mapper.prepare_circuit_inputs(record, "DELETE")
        
        # Validate
        assert self.mapper.validate_circuit_inputs(inputs)
        
        # Check that redacted data is empty
        redacted_str = self.mapper.apply_redaction(
            self.mapper.serialize_medical_data(record),
            "DELETE"
        )
        assert json.loads(redacted_str) == {}
    
    def test_full_redaction_workflow_anonymize(self):
        """Test complete ANONYMIZE workflow."""
        record = {
            "patient_id": "WORKFLOW_002",
            "diagnosis": "Public diagnosis",
            "treatment": "Public treatment",
            "physician": "Dr. Public"
        }
        
        # Prepare inputs
        inputs = self.mapper.prepare_circuit_inputs(record, "ANONYMIZE")
        
        # Validate
        assert self.mapper.validate_circuit_inputs(inputs)
        
        # Check anonymization preserves patient ID
        redacted_str = self.mapper.apply_redaction(
            self.mapper.serialize_medical_data(record),
            "ANONYMIZE"
        )
        redacted = json.loads(redacted_str)
        assert redacted["patient_id"] == "WORKFLOW_002"
        assert redacted["diagnosis"] == "[REDACTED]"
    
    def test_consistency_across_operations(self):
        """Test consistency of hashes across prepare and apply operations."""
        record = {
            "patient_id": "CONSISTENCY_001",
            "diagnosis": "Test",
            "treatment": "Test",
            "physician": "Test"
        }
        
        # Prepare inputs (computes hashes internally)
        inputs = self.mapper.prepare_circuit_inputs(record, "MODIFY")
        
        # Manually compute original hash
        original_str = self.mapper.serialize_medical_data(record)
        import hashlib
        manual_hash = hashlib.sha256(original_str.encode()).hexdigest()
        manual_limb0, manual_limb1 = self.mapper.split_256bit_hash(manual_hash)
        
        # Should match
        assert inputs.public_inputs["originalHash0"] == manual_limb0
        assert inputs.public_inputs["originalHash1"] == manual_limb1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
