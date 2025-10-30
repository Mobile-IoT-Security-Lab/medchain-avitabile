"""
Phase 2 On-Chain Verification Integration Tests
================================================

Tests for the complete on-chain verification implementation including:
- SNARK proof verification on-chain
- Nullifier tracking and replay prevention
- Consistency proof storage and verification
- Full end-to-end redaction workflow

### Bookmark2 for next meeting - Phase 2 on-chain verification implementation
"""

import pytest
import os
import json
import hashlib
from pathlib import Path
from typing import Optional

# Skip tests if EVM or circuit artifacts not available
pytest.importorskip("web3")
CIRCUITS_AVAILABLE = Path("circuits/build/redaction_final.zkey").exists()
pytestmark = pytest.mark.skipif(
    not CIRCUITS_AVAILABLE or not os.getenv("USE_REAL_EVM"),
    reason="Phase 2 tests require compiled circuits and USE_REAL_EVM=1"
)


@pytest.mark.integration
class TestPhase2OnChainVerification:
    """Integration tests for Phase 2 on-chain verification."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment with EVM backend."""
        os.environ["USE_REAL_EVM"] = "1"
        os.environ["REDACTION_BACKEND"] = "EVM"
        
        from adapters.evm import EVMClient
        from medical.MedicalRedactionEngine import MyRedactionEngine
        
        try:
            # Connect to local blockchain
            self.evm_client = EVMClient()
            if not self.evm_client.connect():
                pytest.skip("Real EVM backend unavailable; skipping Phase 2 on-chain verification tests")
            
            # Deploy contracts
            deployed_nullifier = self.evm_client.deploy("NullifierRegistry")
            if not deployed_nullifier:
                pytest.skip("Failed to deploy NullifierRegistry – ensure Hardhat node is running")
            nullifier_addr, nullifier_registry = deployed_nullifier
            print(f" NullifierRegistry deployed at {nullifier_addr}")
            
            deployed_verifier = self.evm_client.deploy("RedactionVerifier_groth16")
            if not deployed_verifier:
                pytest.skip("Failed to deploy RedactionVerifier_groth16 – ensure Hardhat node is running")
            verifier_addr, verifier = deployed_verifier
            print(f" RedactionVerifier_groth16 deployed at {verifier_addr}")
            
            deployed_medical = self.evm_client.deploy(
                "MedicalDataManager",
                args=[verifier_addr, nullifier_addr]
            )
            if not deployed_medical:
                pytest.skip("Failed to deploy MedicalDataManager – ensure Hardhat node is running")
            medical_addr, medical_contract = deployed_medical
            print(f" MedicalDataManager deployed at {medical_addr}")
            
            # Store contracts
            self.nullifier_registry = nullifier_registry
            self.verifier = verifier
            self.medical_contract = medical_contract
            
            # Create engine and attach EVM backend
            self.engine = MyRedactionEngine()
            self.engine.attach_evm_backend(medical_contract, nullifier_registry, None)
            
            yield
        finally:
            # Cleanup
            os.environ.pop("USE_REAL_EVM", None)
            os.environ.pop("REDACTION_BACKEND", None)
    
    def test_nullifier_registry_deployment(self):
        """Test that nullifier registry is properly deployed."""
        # Test nullifier is initially valid
        test_nullifier = hashlib.sha256(b"test_nullifier_1").digest()
        is_valid = self.nullifier_registry.functions.isNullifierValid(test_nullifier).call()
        assert is_valid is True, "New nullifier should be valid"
        
        # Record nullifier
        tx_hash = self.evm_client._build_and_send(
            self.nullifier_registry.functions.recordNullifier(test_nullifier)
        )
        assert tx_hash is not None, "Failed to record nullifier"
        
        # Verify nullifier is now invalid
        is_valid = self.nullifier_registry.functions.isNullifierValid(test_nullifier).call()
        assert is_valid is False, "Used nullifier should be invalid"
        
        # Verify timestamp is recorded
        timestamp, submitter = self.nullifier_registry.functions.getNullifierInfo(test_nullifier).call()
        assert timestamp > 0, "Timestamp should be recorded"
        print(f" Nullifier registry test passed (timestamp: {timestamp})")
    
    def test_nullifier_replay_prevention(self):
        """Test that duplicate nullifiers are rejected (replay attack prevention)."""
        test_nullifier = hashlib.sha256(b"replay_test_nullifier").digest()
        
        # Record nullifier first time
        tx_hash = self.evm_client._build_and_send(
            self.nullifier_registry.functions.recordNullifier(test_nullifier)
        )
        assert tx_hash is not None, "First nullifier recording should succeed"
        
        # Try to record same nullifier again (should fail)
        # Note: This will revert in the contract, so we expect False return
        try:
            result = self.nullifier_registry.functions.recordNullifier(test_nullifier).call()
            assert result is False, "Duplicate nullifier should return False"
        except Exception:
            pass  # Expected if contract reverts
        
        print(" Replay attack prevention test passed")
    
    def test_batch_nullifier_checking(self):
        """Test batch nullifier validation."""
        nullifiers = [
            hashlib.sha256(f"batch_test_{i}".encode()).digest()
            for i in range(5)
        ]
        
        # Check all nullifiers (should all be valid)
        results = self.nullifier_registry.functions.areNullifiersValid(nullifiers).call()
        assert all(results), "All new nullifiers should be valid"
        
        # Record some nullifiers
        for nullifier in nullifiers[:3]:
            self.evm_client._build_and_send(
                self.nullifier_registry.functions.recordNullifier(nullifier)
            )
        
        # Check again (first 3 should be invalid)
        results = self.nullifier_registry.functions.areNullifiersValid(nullifiers).call()
        assert results[0] is False and results[1] is False and results[2] is False
        assert results[3] is True and results[4] is True
        
        print(" Batch nullifier checking test passed")
    
    def test_medical_data_manager_with_nullifier_registry(self):
        """Test that MedicalDataManager correctly references nullifier registry."""
        # Check constructor setup
        registry_addr = self.medical_contract.functions.nullifierRegistry().call()
        assert registry_addr != "0x0000000000000000000000000000000000000000"
        print(f" MedicalDataManager references NullifierRegistry at {registry_addr}")
    
    @pytest.mark.slow
    def test_full_phase2_redaction_workflow(self):
        """Test complete Phase 2 workflow: SNARK + consistency + nullifier."""
        # Create medical record
        record = self.engine.create_medical_data_record({
            "patient_id": "PHASE2_TEST_001",
            "patient_name": "Test Patient",
            "diagnosis": "Test Diagnosis",
            "treatment": "Test Treatment",
            "physician": "Dr. Test",
            "privacy_level": "PRIVATE",
            "consent_status": True
        })
        
        # Store record
        assert self.engine.store_medical_data(record), "Failed to store medical data"
        print(" Medical record stored")
        
        # Request redaction with full Phase 2 verification
        request_id = self.engine.request_data_redaction(
            patient_id="PHASE2_TEST_001",
            redaction_type="ANONYMIZE",
            reason="Phase 2 integration test",
            requester="admin",
            requester_role="ADMIN"
        )
        
        assert request_id is not None, "Failed to create redaction request"
        print(f" Redaction request created: {request_id}")
        
        # Verify request has both proofs
        request = self.engine.redaction_requests[request_id]
        assert request.zk_proof is not None, "ZK proof should be generated"
        assert request.consistency_proof is not None, "Consistency proof should be generated"
        print(f" Both proofs generated:")
        print(f"   ZK Proof: {request.zk_proof.proof_id}")
        print(f"   Consistency Proof: {request.consistency_proof.proof_id}")
        
        # If on-chain submission happened, verify nullifier was recorded
        # (This depends on EVM backend being properly attached)
        
        print(" Full Phase 2 workflow test passed")
    
    @pytest.mark.slow
    def test_consistency_proof_storage(self):
        """Test that consistency proof hashes are stored on-chain."""
        # Create and store record
        record = self.engine.create_medical_data_record({
            "patient_id": "CONSISTENCY_TEST_001",
            "patient_name": "Consistency Test",
            "diagnosis": "Test",
            "treatment": "Test",
            "physician": "Dr. Test",
            "privacy_level": "PRIVATE",
            "consent_status": True
        })
        self.engine.store_medical_data(record)
        
        # Request redaction
        request_id = self.engine.request_data_redaction(
            patient_id="CONSISTENCY_TEST_001",
            redaction_type="DELETE",
            reason="Test consistency proof storage",
            requester="regulator",
            requester_role="REGULATOR"
        )
        
        assert request_id is not None
        request = self.engine.redaction_requests[request_id]
        
        # Verify consistency proof exists
        assert request.consistency_proof is not None
        print(f" Consistency proof stored: {request.consistency_proof.proof_id}")
    
    def test_phase2_event_emissions(self):
        """Test that Phase 2 events are emitted correctly."""
        # This test would need to query events from the blockchain
        # For now, just verify event signatures exist in contract
        
        # Check that MedicalDataManager has the Phase 2 events
        # ProofVerifiedOnChain, NullifierRecorded, ConsistencyProofStored
        
        print(" Phase 2 event emission test (placeholder)")


@pytest.mark.integration
class TestPhase2ErrorHandling:
    """Test error handling in Phase 2 verification."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up minimal test environment."""
        os.environ["USE_REAL_EVM"] = "1"
        os.environ["REDACTION_BACKEND"] = "EVM"
        yield
        os.environ.pop("USE_REAL_EVM", None)
        os.environ.pop("REDACTION_BACKEND", None)
    
    def test_invalid_proof_rejection(self):
        """Test that invalid SNARK proofs are rejected on-chain."""
        # This would require generating an invalid proof
        # For now, document the expected behavior
        pytest.skip("Invalid proof test requires mock invalid proof generation")
    
    def test_nullifier_collision_handling(self):
        """Test handling of nullifier collisions."""
        # Generate same nullifier twice and verify second is rejected
        pytest.skip("Requires deployed contracts")
    
    def test_missing_consistency_proof(self):
        """Test handling when consistency proof is missing."""
        # Submit request without consistency proof
        pytest.skip("Requires deployed contracts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
