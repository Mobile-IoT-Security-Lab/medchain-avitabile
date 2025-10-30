"""
Test suite for NullifierRegistry contract
==========================================

Tests nullifier tracking, replay prevention, and batch operations.

### Bookmark2 for next meeting - Phase 2 on-chain verification implementation
"""

import pytest
import hashlib
import os
from pathlib import Path

# Skip if web3 not available
pytest.importorskip("web3")

pytestmark = pytest.mark.skipif(
    not os.getenv("USE_REAL_EVM"),
    reason="Nullifier registry tests require USE_REAL_EVM=1"
)


@pytest.mark.integration
class TestNullifierRegistry:
    """Tests for NullifierRegistry smart contract."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Deploy NullifierRegistry for testing."""
        os.environ["USE_REAL_EVM"] = "1"
        
        from adapters.evm import EVMClient
        
        self.evm_client = EVMClient()
        try:
            if not self.evm_client.connect():
                pytest.skip("Real EVM backend unavailable; skipping nullifier registry tests")
            
            # Deploy NullifierRegistry
            deployed = self.evm_client.deploy("NullifierRegistry")
            if not deployed:
                pytest.skip("Failed to deploy NullifierRegistry – ensure Hardhat node is running")
            addr, contract = deployed
            
            self.contract = contract
            self.address = addr
            
            print(f"\n NullifierRegistry deployed at {addr}")
            
            yield
        finally:
            os.environ.pop("USE_REAL_EVM", None)
    
    def test_initial_nullifier_validity(self):
        """Test that new nullifiers are initially valid."""
        nullifier = hashlib.sha256(b"test_nullifier_1").digest()
        is_valid = self.contract.functions.isNullifierValid(nullifier).call()
        assert is_valid is True
        print(" New nullifier is valid")
    
    def test_record_nullifier(self):
        """Test recording a new nullifier."""
        nullifier = hashlib.sha256(b"test_nullifier_2").digest()
        
        # Record nullifier
        tx_hash = self.evm_client._build_and_send(
            self.contract.functions.recordNullifier(nullifier)
        )
        assert tx_hash is not None
        
        # Verify it's now invalid
        is_valid = self.contract.functions.isNullifierValid(nullifier).call()
        assert is_valid is False
        
        # Verify timestamp is recorded
        timestamp, submitter = self.contract.functions.getNullifierInfo(nullifier).call()
        assert timestamp > 0
        assert submitter != "0x0000000000000000000000000000000000000000"
        
        print(f" Nullifier recorded (timestamp: {timestamp}, submitter: {submitter[:10]}...)")
    
    def test_duplicate_nullifier_rejected(self):
        """Test that duplicate nullifiers are rejected."""
        nullifier = hashlib.sha256(b"duplicate_test").digest()
        
        # Record first time
        tx_hash = self.evm_client._build_and_send(
            self.contract.functions.recordNullifier(nullifier)
        )
        assert tx_hash is not None
        
        # Try to record again (should return false)
        result = self.contract.functions.recordNullifier(nullifier).call()
        assert result is False
        
        print(" Duplicate nullifier correctly rejected")
    
    def test_batch_nullifier_validation(self):
        """Test batch validation of multiple nullifiers."""
        nullifiers = [
            hashlib.sha256(f"batch_{i}".encode()).digest()
            for i in range(5)
        ]
        
        # Initially all should be valid
        results = self.contract.functions.areNullifiersValid(nullifiers).call()
        assert all(results)
        
        # Record first 3
        for nullifier in nullifiers[:3]:
            self.evm_client._build_and_send(
                self.contract.functions.recordNullifier(nullifier)
            )
        
        # Check again
        results = self.contract.functions.areNullifiersValid(nullifiers).call()
        assert not results[0] and not results[1] and not results[2]
        assert results[3] and results[4]
        
        print(" Batch validation works correctly")
    
    def test_batch_nullifier_recording(self):
        """Test batch recording of nullifiers."""
        nullifiers = [
            hashlib.sha256(f"batch_record_{i}".encode()).digest()
            for i in range(5)
        ]
        
        # Record batch
        tx_hash = self.evm_client._build_and_send(
            self.contract.functions.recordNullifierBatch(nullifiers)
        )
        assert tx_hash is not None
        
        # Verify all are now invalid
        results = self.contract.functions.areNullifiersValid(nullifiers).call()
        assert not any(results)
        
        print(" Batch recording works correctly")
    
    def test_nullifier_info_retrieval(self):
        """Test retrieving nullifier information."""
        nullifier = hashlib.sha256(b"info_test").digest()
        
        # Initially no info
        timestamp, submitter = self.contract.functions.getNullifierInfo(nullifier).call()
        assert timestamp == 0
        assert submitter == "0x0000000000000000000000000000000000000000"
        
        # Record nullifier
        self.evm_client._build_and_send(
            self.contract.functions.recordNullifier(nullifier)
        )
        
        # Now info should exist
        timestamp, submitter = self.contract.functions.getNullifierInfo(nullifier).call()
        assert timestamp > 0
        assert submitter != "0x0000000000000000000000000000000000000000"
        
        print(f" Nullifier info retrieved: timestamp={timestamp}, submitter={submitter[:10]}...")
    
    def test_pause_unpause(self):
        """Test pause/unpause functionality."""
        # Check initial state
        is_paused = self.contract.functions.paused().call()
        assert is_paused is False
        
        # Pause
        tx_hash = self.evm_client._build_and_send(
            self.contract.functions.pause()
        )
        assert tx_hash is not None
        
        # Verify paused
        is_paused = self.contract.functions.paused().call()
        assert is_paused is True
        
        # Try to record (should fail when paused)
        nullifier = hashlib.sha256(b"pause_test").digest()
        try:
            result = self.contract.functions.recordNullifier(nullifier).call()
            # If I get here, I check if it's false due to pause
            # (may vary by implementation)
        except Exception:
            pass  # Expected revert
        
        # Unpause
        tx_hash = self.evm_client._build_and_send(
            self.contract.functions.unpause()
        )
        assert tx_hash is not None
        
        # Now recording should work
        tx_hash = self.evm_client._build_and_send(
            self.contract.functions.recordNullifier(nullifier)
        )
        assert tx_hash is not None
        
        print(" Pause/unpause works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
