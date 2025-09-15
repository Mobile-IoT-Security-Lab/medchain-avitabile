"""
Cross-Component Integration Tests: IPFS ↔ EVM
==============================================

Tests the integration between IPFS and EVM components:
- CID storage and retrieval
- Medical data lifecycle with blockchain pointers
- Data consistency across both systems
- Error handling and edge cases
"""

import pytest
import json
import hashlib
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
import tempfile
import os

# Import adapters
from adapters.ipfs import get_ipfs_client
from adapters.evm import EVMClient
from adapters.config import env_bool

# Import medical components
from medical.MedicalDataIPFS import IPFSMedicalDataManager, FakeIPFSClient, MedicalDataset
from medical.MedicalRedactionEngine import MyRedactionEngine, MedicalDataRecord


class TestIPFSEVMIntegration:
    """Test IPFS and EVM integration scenarios."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        # Use simulation mode for reliable testing
        self.use_real_ipfs = env_bool('USE_REAL_IPFS', False)
        self.use_real_evm = env_bool('USE_REAL_EVM', False)
        
        # Initialize IPFS client
        self.ipfs_client = get_ipfs_client()
        
        # Initialize EVM client (simulation mode)
        self.evm_client = EVMClient()
        
        # Initialize medical data manager
        self.medical_manager = IPFSMedicalDataManager(ipfs_client=self.ipfs_client)
        
        # Test data
        self.test_medical_data = {
            "patient_id": "IPFS_EVM_TEST_001",
            "patient_name": "Integration Test Patient",
            "medical_record_number": "MRN_IPFS_EVM_001",
            "diagnosis": "Integration test diagnosis",
            "treatment": "Integration test treatment",
            "physician": "Dr. Integration Test",
            "date_of_birth": "1990-01-01",
            "medical_history": ["Previous condition 1", "Previous condition 2"],
            "lab_results": {
                "blood_pressure": "120/80",
                "heart_rate": "72",
                "temperature": "98.6"
            }
        }
    
    def test_ipfs_cid_storage_and_evm_pointer(self):
        """Test storing data in IPFS and saving CID on EVM."""
        # Step 1: Create medical dataset and upload to IPFS
        dataset = MedicalDataset(
            dataset_id="integration_test_dataset",
            name="Integration Test Dataset",
            description="Test dataset for IPFS-EVM integration",
            patient_records=[self.test_medical_data],
            creation_timestamp=int(time.time()),
            last_updated=int(time.time()),
            version="1.0"
        )
        
        cid = self.medical_manager.upload_dataset(dataset)
        assert cid is not None
        assert isinstance(cid, str)
        assert len(cid) > 0
        
        # Step 2: Store CID on EVM (simulate smart contract storage)
        if self.evm_client.enabled:
            # Real EVM integration
            tx_receipt = self.evm_client.store_medical_data_pointer(
                patient_id=self.test_medical_data["patient_id"],
                ipfs_cid=cid,
                data_hash=hashlib.sha256(json.dumps(self.test_medical_data, sort_keys=True).encode()).hexdigest()
            )
            assert tx_receipt is not None
        else:
            # Simulated EVM storage
            storage_result = self._simulate_evm_cid_storage(
                patient_id=self.test_medical_data["patient_id"],
                cid=cid
            )
            assert storage_result["success"] is True
            assert storage_result["cid"] == cid
        
        # Step 3: Retrieve CID from EVM and fetch data from IPFS
        stored_cid = self._get_cid_from_evm(self.test_medical_data["patient_id"])
        assert stored_cid == cid
        
        # Step 4: Download data from IPFS using retrieved CID
        retrieved_dataset = self.medical_manager.download_dataset(stored_cid)
        assert retrieved_dataset is not None
        assert retrieved_dataset.dataset_id == "integration_test_dataset"
        assert len(retrieved_dataset.patient_records) == 1
        assert retrieved_dataset.patient_records[0]["patient_id"] == self.test_medical_data["patient_id"]
    
    def test_medical_data_lifecycle_ipfs_evm(self):
        """Test complete medical data lifecycle across IPFS and EVM."""
        # Create medical record
        medical_record = MedicalDataRecord(
            patient_id=self.test_medical_data["patient_id"],
            data=self.test_medical_data,
            ipfs_cid=None,
            blockchain_tx_hash=None
        )
        
        # Step 1: Store in IPFS
        dataset = MedicalDataset(
            dataset_id=f"lifecycle_{medical_record.patient_id}",
            records=[self.test_medical_data],
            metadata={"test": "lifecycle"}
        )
        cid = self.medical_manager.upload_dataset(dataset)
        medical_record.ipfs_cid = cid
        
        # Step 2: Register on blockchain
        if self.evm_client.enabled:
            tx_hash = self.evm_client.register_medical_record(
                patient_id=medical_record.patient_id,
                ipfs_cid=cid,
                data_hash=medical_record.get_data_hash()
            )
            medical_record.blockchain_tx_hash = tx_hash
        else:
            # Simulate blockchain registration
            tx_hash = f"0x{''.join(['a'] * 64)}"  # Mock transaction hash
            medical_record.blockchain_tx_hash = tx_hash
        
        # Step 3: Verify data consistency
        # Retrieve from IPFS using stored CID
        ipfs_dataset = self.medical_manager.download_dataset(cid)
        assert ipfs_dataset.records[0]["patient_id"] == medical_record.patient_id
        
        # Verify blockchain record exists
        blockchain_record = self._get_blockchain_record(medical_record.patient_id)
        assert blockchain_record["ipfs_cid"] == cid
        assert blockchain_record["tx_hash"] == tx_hash
        
        # Step 4: Update medical record
        updated_data = self.test_medical_data.copy()
        updated_data["treatment"] = "Updated integration test treatment"
        updated_data["last_updated"] = "2025-09-15"
        
        # Upload updated version to IPFS
        updated_dataset = MedicalDataset(
            dataset_id=f"updated_{medical_record.patient_id}",
            records=[updated_data],
            metadata={"test": "updated", "version": "2"}
        )
        new_cid = self.medical_manager.upload_dataset(updated_dataset)
        
        # Update blockchain pointer
        if self.evm_client.enabled:
            update_tx_hash = self.evm_client.update_medical_record_pointer(
                patient_id=medical_record.patient_id,
                new_ipfs_cid=new_cid,
                new_data_hash=hashlib.sha256(json.dumps(updated_data, sort_keys=True).encode()).hexdigest()
            )
        else:
            update_tx_hash = f"0x{''.join(['b'] * 64)}"  # Mock update transaction
        
        # Verify updated data
        final_dataset = self.medical_manager.download_dataset(new_cid)
        final_data = final_dataset.records[0]
        assert final_data["treatment"] == "Updated integration test treatment"
        assert final_data["last_updated"] == "2025-09-15"
    
    def test_ipfs_evm_error_handling(self):
        """Test error handling in IPFS-EVM integration scenarios."""
        
        # Test 1: IPFS upload failure
        with patch.object(self.ipfs_client, 'add', side_effect=Exception("IPFS connection failed")):
            with pytest.raises(Exception) as exc_info:
                dataset = MedicalDataset(
                    dataset_id="failed_upload_test",
                    records=[self.test_medical_data],
                    metadata={"test": "failure"}
                )
                self.medical_manager.upload_dataset(dataset)
            assert "IPFS connection failed" in str(exc_info.value)
        
        # Test 2: Invalid CID handling
        invalid_cid = "invalid_cid_format"
        with pytest.raises(Exception):
            self.medical_manager.download_dataset(invalid_cid)
        
        # Test 3: EVM transaction failure (if using real EVM)
        if self.evm_client.enabled:
            with patch.object(self.evm_client, 'store_medical_data_pointer', side_effect=Exception("EVM transaction failed")):
                with pytest.raises(Exception) as exc_info:
                    self.evm_client.store_medical_data_pointer(
                        patient_id="FAIL_TEST_001",
                        ipfs_cid="QmTest123",
                        data_hash="test_hash"
                    )
                assert "EVM transaction failed" in str(exc_info.value)
    
    def test_data_consistency_validation(self):
        """Test data consistency validation between IPFS and EVM."""
        # Upload data to IPFS
        dataset = MedicalDataset(
            dataset_id="consistency_test_dataset", 
            records=[self.test_medical_data],
            metadata={"test": "consistency"}
        )
        cid = self.medical_manager.upload_dataset(dataset)
        
        # Calculate data hash
        original_hash = hashlib.sha256(
            json.dumps(self.test_medical_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Store on EVM with correct hash
        self._simulate_evm_cid_storage(
            patient_id=self.test_medical_data["patient_id"],
            cid=cid,
            data_hash=original_hash
        )
        
        # Verify consistency
        consistency_check = self._verify_ipfs_evm_consistency(
            patient_id=self.test_medical_data["patient_id"]
        )
        assert consistency_check["consistent"] is True
        assert consistency_check["ipfs_hash"] == consistency_check["evm_hash"]
        
        # Test inconsistency detection
        # Modify data in IPFS (simulate corruption)
        corrupted_data = self.test_medical_data.copy()
        corrupted_data["diagnosis"] = "CORRUPTED DATA"
        
        corrupted_dataset = MedicalDataset(
            dataset_id="corrupted_test_dataset",
            records=[corrupted_data],
            metadata={"test": "corrupted"}
        )
        corrupted_cid = self.medical_manager.upload_dataset(corrupted_dataset)
        
        # Update EVM with new CID but old hash (simulate inconsistency)
        self._simulate_evm_cid_storage(
            patient_id=self.test_medical_data["patient_id"],
            cid=corrupted_cid,
            data_hash=original_hash  # Old hash doesn't match new data
        )
        
        # Verify inconsistency is detected
        inconsistency_check = self._verify_ipfs_evm_consistency(
            patient_id=self.test_medical_data["patient_id"]
        )
        assert inconsistency_check["consistent"] is False
    
    def test_bulk_operations_ipfs_evm(self):
        """Test bulk operations across IPFS and EVM."""
        # Create multiple test records
        test_records = []
        for i in range(5):
            record_data = self.test_medical_data.copy()
            record_data["patient_id"] = f"BULK_TEST_{i:03d}"
            record_data["medical_record_number"] = f"MRN_BULK_{i:03d}"
            test_records.append(record_data)
        
        # Bulk upload to IPFS and register on EVM
        cids = []
        tx_hashes = []
        
        for record_data in test_records:
            # Upload to IPFS
            dataset = MedicalDataset(
                dataset_id=f"bulk_test_{record_data['patient_id']}",
                records=[record_data],
                metadata={"test": "bulk", "patient_id": record_data["patient_id"]}
            )
            cid = self.medical_manager.upload_dataset(dataset)
            cids.append(cid)
            
            # Register on EVM
            if self.evm_client.enabled:
                tx_hash = self.evm_client.register_medical_record(
                    patient_id=record_data["patient_id"],
                    ipfs_cid=cid,
                    data_hash=hashlib.sha256(json.dumps(record_data, sort_keys=True).encode()).hexdigest()
                )
            else:
                tx_hash = f"0x{''.join([hex(i)[2:] for _ in range(32)])}"
            tx_hashes.append(tx_hash)
        
        # Verify all records
        for i, record_data in enumerate(test_records):
            # Verify IPFS data
            retrieved_dataset = self.medical_manager.download_dataset(cids[i])
            retrieved_data = retrieved_dataset.records[0]
            assert retrieved_data["patient_id"] == record_data["patient_id"]
            
            # Verify EVM record
            blockchain_record = self._get_blockchain_record(record_data["patient_id"])
            assert blockchain_record["ipfs_cid"] == cids[i]
            assert blockchain_record["tx_hash"] == tx_hashes[i]
    
    def _simulate_evm_cid_storage(self, patient_id: str, cid: str, data_hash: Optional[str] = None) -> Dict[str, Any]:
        """Simulate EVM CID storage for testing."""
        if not hasattr(self, '_evm_storage'):
            self._evm_storage = {}
        
        self._evm_storage[patient_id] = {
            "cid": cid,
            "data_hash": data_hash,
            "timestamp": "2025-09-15T10:00:00Z",
            "tx_hash": f"0x{''.join(['a'] * 64)}"
        }
        
        return {"success": True, "cid": cid, "patient_id": patient_id}
    
    def _get_cid_from_evm(self, patient_id: str) -> Optional[str]:
        """Get CID from EVM storage (real or simulated)."""
        if self.evm_client.enabled:
            # Real EVM query
            return self.evm_client.get_medical_record_cid(patient_id)
        else:
            # Simulated EVM query
            if hasattr(self, '_evm_storage') and patient_id in self._evm_storage:
                return self._evm_storage[patient_id]["cid"]
            return None
    
    def _get_blockchain_record(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get complete blockchain record."""
        if self.evm_client.enabled:
            return self.evm_client.get_medical_record(patient_id)
        else:
            if hasattr(self, '_evm_storage') and patient_id in self._evm_storage:
                return self._evm_storage[patient_id]
            return None
    
    def _verify_ipfs_evm_consistency(self, patient_id: str) -> Dict[str, Any]:
        """Verify data consistency between IPFS and EVM."""
        # Get CID from EVM
        evm_record = self._get_blockchain_record(patient_id)
        if not evm_record:
            return {"consistent": False, "error": "No EVM record found"}
        
        cid = evm_record["cid"]
        evm_hash = evm_record.get("data_hash")
        
        # Get data from IPFS
        try:
            ipfs_dataset = self.medical_manager.download_dataset(cid)
            ipfs_data = ipfs_dataset.records[0] if ipfs_dataset.records else {}
            ipfs_hash = hashlib.sha256(
                json.dumps(ipfs_data, sort_keys=True).encode()
            ).hexdigest()
            
            return {
                "consistent": ipfs_hash == evm_hash if evm_hash else True,
                "ipfs_hash": ipfs_hash,
                "evm_hash": evm_hash,
                "cid": cid
            }
        except Exception as e:
            return {"consistent": False, "error": f"IPFS retrieval failed: {e}"}


@pytest.mark.integration
class TestIPFSEVMRealIntegration:
    """Integration tests requiring real IPFS and EVM services."""
    
    @pytest.mark.requires_ipfs
    @pytest.mark.requires_evm
    def test_real_ipfs_evm_integration(self):
        """Test with real IPFS and EVM services."""
        # This test only runs when both real services are available
        ipfs_client = get_ipfs_client()  # Should be real client
        evm_client = EVMClient()  # Should be real client
        
        assert ipfs_client.__class__.__name__ != "FakeIPFSClient"
        assert evm_client.enabled is True
        
        # Test basic integration
        test_data = {"test": "real_integration", "timestamp": "2025-09-15"}
        
        # Upload to real IPFS
        medical_manager = IPFSMedicalDataManager(ipfs_client=ipfs_client)
        dataset = MedicalDataset(
            dataset_id="real_test",
            records=[test_data],
            metadata={"test": "real_integration"}
        )
        cid = medical_manager.upload_dataset(dataset)
        
        # Store CID on real EVM
        tx_receipt = evm_client.store_medical_data_pointer(
            patient_id="REAL_TEST_001",
            ipfs_cid=cid,
            data_hash=hashlib.sha256(json.dumps(test_data, sort_keys=True).encode()).hexdigest()
        )
        
        assert tx_receipt is not None
        assert "transactionHash" in tx_receipt
        
        # Retrieve and verify
        stored_cid = evm_client.get_medical_record_cid("REAL_TEST_001")
        assert stored_cid == cid
        
        retrieved_dataset = medical_manager.download_dataset(stored_cid)
        retrieved_data = retrieved_dataset.records[0]
        assert retrieved_data["test"] == "real_integration"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])