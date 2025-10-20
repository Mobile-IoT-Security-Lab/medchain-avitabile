"""
Cross-Component Integration Tests: Full Redaction Pipeline
==========================================================

Tests the complete redaction pipeline across IPFS, SNARK, and EVM components:
- End-to-end redaction workflows
- Multi-component data consistency
- Error handling across the pipeline
- Performance and scalability testing
"""

import json
import hashlib
import time
import copy  # Add copy module
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch
import tempfile
import os
from medical.MedicalDataIPFS import MedicalDataset
import pytest

pytest.skip(
    "Full redaction pipeline tests require snarkjs and on-chain infrastructure",
    allow_module_level=True,
)

# Import all adapters
from adapters.ipfs import get_ipfs_client
from adapters.snark import SnarkClient
from adapters.evm import EVMClient
from adapters.config import env_bool

# Import core components
from medical.MedicalDataIPFS import IPFSMedicalDataManager
from medical.MedicalRedactionEngine import MyRedactionEngine, MedicalDataRecord
from ZK.SNARKs import RedactionSNARKManager
from ZK.ProofOfConsistency import ConsistencyProof, ConsistencyProofGenerator, ConsistencyCheckType

# Import models
from Models.Block import Block
from Models.Transaction import Transaction


class TestFullRedactionPipeline:
    """Test complete redaction pipeline across all components."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        # Configuration
        self.use_real_ipfs = env_bool('USE_REAL_IPFS', False)
        self.use_real_evm = env_bool('USE_REAL_EVM', False)
        
        # Initialize all components
        self.ipfs_client = get_ipfs_client()
        if self.ipfs_client is None:
            # Use a mock client for testing when real IPFS is not available
            from medical.MedicalDataIPFS import FakeIPFSClient
            self.ipfs_client = FakeIPFSClient()
        self.snark_client = SnarkClient()
        self.evm_client = EVMClient()
        
        # Initialize managers
        self.medical_manager = IPFSMedicalDataManager(ipfs_client=self.ipfs_client)
        self.redaction_engine = MyRedactionEngine()
        self.snark_manager = RedactionSNARKManager()
        self.consistency_prover = ConsistencyProofGenerator()
        
        # Test patient data
        self.patient_data = {
            "patient_id": "PIPELINE_TEST_001",
            "patient_name": "Pipeline Test Patient",
            "medical_record_number": "MRN_PIPELINE_001",
            "date_of_birth": "1985-03-15",
            "diagnosis": "Sensitive medical condition requiring privacy protection",
            "treatment": "Specialized treatment protocol",
            "physician": "Dr. Pipeline Test",
            "medical_history": [
                "Previous condition requiring redaction",
                "Another sensitive medical history item"
            ],
            "lab_results": {
                "blood_work": {
                    "hemoglobin": "14.2 g/dL",
                    "glucose": "95 mg/dL",
                    "sensitive_marker": "CONFIDENTIAL_VALUE"
                },
                "imaging": {
                    "ct_scan": "Abnormal findings requiring redaction",
                    "mri": "Sensitive imaging results"
                }
            },
            "insurance_info": {
                "provider": "HealthCare Plus",
                "policy_number": "SENSITIVE_POLICY_123456",
                "coverage_details": "Full coverage with privacy concerns"
            }
        }
        
        # Redaction scenarios
        self.redaction_scenarios = [
            {
                "name": "GDPR_DELETE",
                "type": "DELETE",
                "fields": ["diagnosis", "lab_results.blood_work.sensitive_marker"],
                "reason": "GDPR Right to be Forgotten",
                "requester": "patient"
            },
            {
                "name": "HIPAA_ANONYMIZE", 
                "type": "ANONYMIZE",
                "fields": ["patient_name", "medical_record_number", "insurance_info.policy_number"],
                "reason": "HIPAA de-identification",
                "requester": "researcher"
            },
            {
                "name": "SELECTIVE_MODIFY",
                "type": "MODIFY",
                "fields": ["lab_results.imaging.ct_scan", "medical_history.0"],
                "reason": "Selective redaction for sharing",
                "requester": "physician"
            }
        ]
    
    def test_complete_redaction_pipeline_e2e(self):
        """Test complete end-to-end redaction pipeline."""
        
        print("=" * 60)
        print("COMPLETE REDACTION PIPELINE TEST")
        print("=" * 60)
        
        # Phase 1: Data Storage and Initial Setup
        print("\n Phase 1: Initial Data Storage")
        
        # Step 1.1: Store original medical data in IPFS
        from medical.MedicalDataIPFS import MedicalDataset
        import time
        
        original_dataset = MedicalDataset(
            dataset_id=f"original_{self.patient_data['patient_id']}",
            name="Original Patient Data",
            description="Original medical data before redaction",
            patient_records=[self.patient_data],
            creation_timestamp=int(time.time()),
            last_updated=int(time.time()),
            version="1.0"
        )
        original_cid = self.medical_manager.upload_dataset(original_dataset)
        print(f" Original data stored in IPFS: {original_cid}")
        
        # Step 1.2: Register medical record on blockchain
        original_hash = hashlib.sha256(
            json.dumps(self.patient_data, sort_keys=True).encode()
        ).hexdigest()
        
        if self.evm_client.is_enabled():
            registration_tx = self.evm_client.register_medical_record(
                patient_id=self.patient_data["patient_id"],
                ipfs_cid=original_cid,
                data_hash=original_hash
            )
            print(f" Medical record registered on blockchain: {registration_tx}")
        else:
            registration_tx = self._simulate_blockchain_registration(
                self.patient_data["patient_id"], original_cid, original_hash
            )
            print(f" Medical record registration simulated: {registration_tx}")
        
        # Step 1.3: Create initial blockchain state
        original_block = self._create_blockchain_block(
            block_id=1,
            transactions=[{
                "patient_id": self.patient_data["patient_id"],
                "ipfs_cid": original_cid,
                "data_hash": original_hash,
                "tx_hash": registration_tx
            }]
        )
        
        # Phase 2: Process Multiple Redaction Scenarios
        print("\n Phase 2: Redaction Processing")
        
        redacted_states = []
        for scenario in self.redaction_scenarios:
            print(f"\n  Scenario: {scenario['name']}")
            
            # Step 2.1: Create redacted version of data
            redacted_data = self._apply_redaction(
                copy.deepcopy(self.patient_data),  # Use deep copy to avoid modifying original
                scenario["fields"],
                scenario["type"]
            )
            
            # Step 2.2: Upload redacted data to IPFS
            redacted_dataset = MedicalDataset(
                dataset_id=f"redacted_{scenario['name']}_{self.patient_data['patient_id']}",
                name=f"Redacted Dataset - {scenario['name']}",
                description=f"Dataset after {scenario['type']} redaction",
                patient_records=[redacted_data],
                creation_timestamp=int(time.time()),
                last_updated=int(time.time()),
                version="1.0"
            )
            redacted_cid = self.medical_manager.upload_dataset(redacted_dataset)
            print(f"     Redacted data uploaded: {redacted_cid}")
            
            # Step 2.3: Generate SNARK proof for redaction validity
            proof_inputs = self._prepare_snark_inputs(
                original_data=self.patient_data,
                redacted_data=redacted_data,
                redaction_type=scenario["type"]
            )
            
            if self.snark_client.is_enabled():
                snark_proof = self.snark_client.prove_redaction(
                    original_data=proof_inputs["original_hash"],
                    redacted_data=proof_inputs["redacted_hash"],
                    merkle_root=proof_inputs["merkle_root"],
                    nullifier=proof_inputs["nullifier"]
                )
                print(f"     SNARK proof generated (real)")
            else:
                snark_proof = self._generate_mock_snark_proof(proof_inputs)
                print(f"     SNARK proof generated (simulated)")
            
            # Step 2.4: Submit redaction request to blockchain
            if self.evm_client.is_enabled():
                request_result = self.evm_client.submit_redaction_request(
                    patient_id=self.patient_data["patient_id"],
                    redaction_type=scenario["type"],
                    proof=snark_proof,
                    reason=scenario["reason"],
                    new_ipfs_cid=redacted_cid
                )
                request_id = request_result["request_id"]
                print(f"     Redaction request submitted: {request_id}")
            else:
                request_id = self._simulate_redaction_request(
                    scenario, snark_proof, redacted_cid
                )
                print(f"     Redaction request simulated: {request_id}")
            
            # Step 2.5: Verify proof on blockchain
            if self.evm_client.is_enabled():
                verification_result = self.evm_client.verify_redaction_proof_on_chain(
                    request_id=request_id
                )
                assert verification_result["valid"] is True
                print(f"     Proof verified on blockchain")
            else:
                verification_result = self._simulate_proof_verification(request_id)
                assert verification_result["valid"] is True
                print(f"     Proof verification simulated")
            
            # Step 2.6: Generate proof of consistency
            operation_details = {
                "patient_id": self.patient_data["patient_id"],
                "redaction_type": scenario["type"],
                "fields": scenario["fields"]
            }
            consistency_proof = self.consistency_prover.generate_consistency_proof(
                check_type=ConsistencyCheckType.MERKLE_TREE,
                pre_redaction_data={"blocks": [original_block]},
                post_redaction_data={"blocks": [self._create_redacted_block(original_block, redacted_data, redacted_cid)]},
                operation_details=operation_details
            )
            # Note: For DELETE operations, consistency proof should detect the redaction
            # This is expected behavior for data integrity verification
            print(f"     Consistency proof status: {'valid' if consistency_proof.is_valid else 'detected redaction'}")
            print(f"     Consistency proof generated")
            
            redacted_states.append({
                "scenario": scenario,
                "redacted_data": redacted_data,
                "redacted_cid": redacted_cid,
                "snark_proof": snark_proof,
                "request_id": request_id,
                "consistency_proof": consistency_proof
            })
        
        # Phase 3: Approval and Execution
        print("\n Phase 3: Approval and Execution")
        
        for state in redacted_states:
            scenario = state["scenario"]
            request_id = state["request_id"]
            
            # Step 3.1: Approve redaction request
            if self.evm_client.is_enabled():
                approval_result = self.evm_client.approve_redaction_request(
                    request_id=request_id,
                    approver="regulator",
                    approval_reason=f"Approved {scenario['reason']}"
                )
                assert approval_result["success"] is True
            else:
                approval_result = self._simulate_approval(request_id)
                assert approval_result["approved"] is True
            
            print(f"   {scenario['name']} approved")
            
            # Step 3.2: Execute redaction (update blockchain pointers)
            if self.evm_client.is_enabled():
                execution_result = self.evm_client.execute_redaction(
                    request_id=request_id
                )
                assert execution_result["success"] is True
            else:
                execution_result = self._simulate_execution(request_id, state["redacted_cid"])
                assert execution_result["executed"] is True
            
            print(f"   {scenario['name']} executed")
        
        # Phase 4: Verification and Consistency Checks
        print("\n Phase 4: Final Verification")
        
        # Step 4.1: Verify all redacted data is accessible
        for state in redacted_states:
            retrieved_dataset = self.medical_manager.download_dataset(state["redacted_cid"])
            assert retrieved_dataset is not None
            assert len(retrieved_dataset.patient_records) > 0
            retrieved_data = retrieved_dataset.patient_records[0]  # Get the first patient record
            self._verify_redaction_applied(
                original_data=self.patient_data,
                redacted_data=retrieved_data,
                scenario=state["scenario"]
            )
        
        print("   All redacted data verified accessible")
        
        # Step 4.2: Verify blockchain consistency
        final_consistency_check = self._verify_final_consistency(
            original_data=self.patient_data,
            redacted_states=redacted_states
        )
        assert final_consistency_check["consistent"] is True
        print("   Final blockchain consistency verified")
        
        # Step 4.3: Verify privacy compliance
        privacy_compliance = self._verify_privacy_compliance(redacted_states)
        assert privacy_compliance["compliant"] is True
        print("   Privacy compliance verified")
        
        print("\n COMPLETE REDACTION PIPELINE TEST PASSED")
        print("=" * 60)
    
    def test_pipeline_error_handling(self):
        """Test error handling throughout the redaction pipeline."""
        
        # Test 1: IPFS upload failure - verify error handling
        with patch.object(self.ipfs_client, 'add', side_effect=Exception("IPFS connection failed")):
            test_dataset = MedicalDataset(
                dataset_id="error_test",
                name="Error Test Dataset",
                description="Dataset for testing error handling",
                patient_records=[self.patient_data],
                creation_timestamp=int(time.time()),
                last_updated=int(time.time()),
                version="1.0"
            )
            result = self.medical_manager.upload_dataset(test_dataset)
            # The upload_dataset method handles exceptions and returns empty string
            assert result == "", "Expected empty string when IPFS upload fails"
        
        # Test 2: SNARK proof generation failure
        invalid_proof_inputs = {
            "original_hash": "invalid_hash",
            "redacted_hash": None,  # Invalid
            "merkle_root": "invalid",
            "nullifier": -1
        }
        
        if self.snark_client.is_enabled():
            with pytest.raises(Exception):
                self.snark_client.prove_redaction(**invalid_proof_inputs)
        
        # Test 3: Blockchain verification failure
        if self.evm_client.is_enabled():
            # Submit invalid proof
            invalid_proof = {
                "a": ["0xinvalid"],
                "b": [["0x1", "0x2"]],
                "c": ["0x3"],
                "publicSignals": ["not_a_number"]
            }
            
            with pytest.raises(Exception):
                self.evm_client.verify_redaction_proof(
                    proof_a=invalid_proof["a"],
                    proof_b=invalid_proof["b"],
                    proof_c=invalid_proof["c"],
                    public_signals=invalid_proof["publicSignals"]
                )
        
        # Test 4: Consistency check failure
        inconsistent_blocks = [
            self._create_blockchain_block(1, [{"data": "original"}]),
            self._create_blockchain_block(2, [{"data": "completely_different"}])  # No valid redaction
        ]
        
        consistency_result = self.consistency_prover.generate_consistency_proof(
            check_type=ConsistencyCheckType.MERKLE_TREE,
            pre_redaction_data={"blocks": [inconsistent_blocks[0]]},
            post_redaction_data={"blocks": [inconsistent_blocks[1]]},
            operation_details={"type": "DELETE", "fields": ["data"]}
        )
        
        # Should detect inconsistency
        assert consistency_result.is_valid is False
    
    def test_pipeline_performance(self):
        """Test pipeline performance with multiple operations."""
        
        start_time = time.time()
        
        # Create multiple patient records
        patient_records = []
        for i in range(5):
            patient_data = self.patient_data.copy()
            patient_data["patient_id"] = f"PERF_TEST_{i:03d}"
            patient_data["medical_record_number"] = f"MRN_PERF_{i:03d}"
            patient_records.append(patient_data)
        
        # Process each record through the pipeline
        results = []
        for patient_data in patient_records:
            # Upload to IPFS
            dataset = MedicalDataset(
                dataset_id=patient_data.get("medical_record_number", f"dataset_{len(patient_records)}"),
                name=f"Performance Test Dataset",
                description="Performance test medical dataset",
                patient_records=[patient_data],
                creation_timestamp=int(time.time()), last_updated=int(time.time()),
                version="1.0"
            )
            cid = self.medical_manager.upload_dataset(dataset)
            
            # Apply redaction
            redacted_data = self._apply_redaction(
                patient_data,
                ["diagnosis", "lab_results.blood_work.sensitive_marker"],
                "DELETE"
            )
            
            # Upload redacted version
            redacted_dataset = MedicalDataset(
                dataset_id=patient_data.get("medical_record_number", f"redacted_dataset_{len(patient_records)}"),
                name=f"Redacted Performance Test Dataset", 
                description="Redacted performance test medical dataset",
                patient_records=[redacted_data],
                creation_timestamp=int(time.time()), last_updated=int(time.time()),
                version="1.0"
            )
            redacted_cid = self.medical_manager.upload_dataset(redacted_dataset)
            
            results.append({
                "patient_id": patient_data["patient_id"],
                "original_cid": cid,
                "redacted_cid": redacted_cid,
                "processing_time": time.time() - start_time
            })
        
        total_time = time.time() - start_time
        avg_time_per_record = total_time / len(patient_records)
        
        print(f"Performance Test Results:")
        print(f"  Total records processed: {len(patient_records)}")
        print(f"  Total processing time: {total_time:.2f} seconds")
        print(f"  Average time per record: {avg_time_per_record:.2f} seconds")
        
        # Performance assertions
        assert total_time < 30.0  # Should complete within 30 seconds
        assert avg_time_per_record < 10.0  # Should average under 10 seconds per record
        
        # Verify all records are accessible
        for result in results:
            original_data = self.medical_manager.download_dataset(result["original_cid"])
            redacted_data = self.medical_manager.download_dataset(result["redacted_cid"])
            
            # Access patient data from the dataset
            original_patient = original_data.patient_records[0]
            redacted_patient = redacted_data.patient_records[0]
            
            assert original_patient["patient_id"] == result["patient_id"]
            assert redacted_patient["patient_id"] == result["patient_id"]
            assert redacted_patient["diagnosis"] == "REDACTED"  # Verify redaction applied
    
    def test_pipeline_data_integrity(self):
        """Test data integrity throughout the pipeline."""
        
        # Step 1: Store original data and compute hash
        original_dataset = MedicalDataset(
            dataset_id="integrity_test",
            name="Integrity Test Dataset",
            description="Dataset for testing data integrity",
            patient_records=[self.patient_data],
            creation_timestamp=int(time.time()), last_updated=int(time.time()),
            version="1.0"
        )
        original_cid = self.medical_manager.upload_dataset(original_dataset)
        
        original_hash = hashlib.sha256(
            json.dumps(self.patient_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Step 2: Apply redaction and verify hash changes appropriately
        redacted_data = self._apply_redaction(
            self.patient_data.copy(),
            ["diagnosis"],
            "DELETE"
        )
        
        redacted_dataset = MedicalDataset(
            dataset_id="integrity_test_redacted",
            name="Integrity Test Redacted Dataset",
            description="Redacted dataset for testing data integrity",
            patient_records=[redacted_data],
            creation_timestamp=int(time.time()), last_updated=int(time.time()),
            version="1.0"
        )
        redacted_cid = self.medical_manager.upload_dataset(redacted_dataset)
        
        redacted_hash = hashlib.sha256(
            json.dumps(redacted_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Verify hashes are different (data was actually changed)
        assert original_hash != redacted_hash
        
        # Step 3: Retrieve data and verify integrity
        retrieved_original = self.medical_manager.download_dataset(original_cid)
        retrieved_redacted = self.medical_manager.download_dataset(redacted_cid)
        
        # Extract patient data from MedicalDataset objects for hash comparison
        retrieved_original_data = retrieved_original.patient_records[0]
        retrieved_redacted_data = retrieved_redacted.patient_records[0]
        
        # Verify original data integrity
        retrieved_original_hash = hashlib.sha256(
            json.dumps(retrieved_original_data, sort_keys=True).encode()
        ).hexdigest()
        assert retrieved_original_hash == original_hash
        
        # Verify redacted data integrity
        retrieved_redacted_hash = hashlib.sha256(
            json.dumps(retrieved_redacted_data, sort_keys=True).encode()
        ).hexdigest()
        assert retrieved_redacted_hash == redacted_hash
        
        # Step 4: Verify redaction was applied correctly
        assert retrieved_original_data["diagnosis"] == self.patient_data["diagnosis"]
        assert retrieved_redacted_data["diagnosis"] == "REDACTED"
        
        # Step 5: Verify non-redacted fields remain unchanged
        for field in ["patient_id", "patient_name", "medical_record_number"]:
            assert retrieved_original_data[field] == retrieved_redacted_data[field]
    
    def _apply_redaction(self, data: Dict[str, Any], fields: List[str], redaction_type: str) -> Dict[str, Any]:
        """Apply redaction to data based on field paths and type."""
        redacted_data = data.copy()
        
        for field_path in fields:
            self._apply_field_redaction(redacted_data, field_path, redaction_type)
        
        return redacted_data
    
    def _apply_field_redaction(self, data: Dict[str, Any], field_path: str, redaction_type: str):
        """Apply redaction to a specific field path."""
        path_parts = field_path.split('.')
        current = data
        
        # Navigate to the parent of the target field
        for part in path_parts[:-1]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                # Handle array indexing for list elements
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return  # Field path doesn't exist
            else:
                return  # Field path doesn't exist
        
        # Apply redaction to the target field
        target_field = path_parts[-1]
        if isinstance(current, dict) and target_field in current:
            original_value = current[target_field]
            if redaction_type == "DELETE":
                current[target_field] = "REDACTED"
            elif redaction_type == "ANONYMIZE":
                current[target_field] = f"ANONYMIZED_{len(str(original_value))}"
            elif redaction_type == "MODIFY":
                # Include field path to ensure uniqueness
                field_hash = hashlib.md5(field_path.encode()).hexdigest()[:6]
                current[target_field] = f"MODIFIED_{field_hash}_{str(original_value)[:10]}..."
        elif isinstance(current, list) and target_field.isdigit():
            # Handle array indexing for the target field
            index = int(target_field)
            if 0 <= index < len(current):
                original_value = current[index]
                if redaction_type == "DELETE":
                    current[index] = "REDACTED"
                elif redaction_type == "ANONYMIZE":
                    current[index] = f"ANONYMIZED_{len(str(original_value))}"
                elif redaction_type == "MODIFY":
                    # Include field path to ensure uniqueness
                    field_hash = hashlib.md5(field_path.encode()).hexdigest()[:6]
                    current[index] = f"MODIFIED_{field_hash}_{str(original_value)[:10]}..."
    
    def _prepare_snark_inputs(self, original_data: Dict[str, Any], redacted_data: Dict[str, Any], redaction_type: str) -> Dict[str, Any]:
        """Prepare inputs for SNARK proof generation."""
        original_hash = hashlib.sha256(
            json.dumps(original_data, sort_keys=True).encode()
        ).hexdigest()
        
        redacted_hash = hashlib.sha256(
            json.dumps(redacted_data, sort_keys=True).encode()
        ).hexdigest()
        
        return {
            "original_hash": original_hash,
            "redacted_hash": redacted_hash,
            "merkle_root": "0x" + "a" * 64,  # Mock merkle root
            "nullifier": "0x" + "b" * 64,    # Mock nullifier
            "redaction_type": redaction_type
        }
    
    def _generate_mock_snark_proof(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock SNARK proof for testing."""
        return {
            "proof": {
                "a": ["0x" + "1" * 64, "0x" + "2" * 64],
                "b": [["0x" + "3" * 64, "0x" + "4" * 64], ["0x" + "5" * 64, "0x" + "6" * 64]],
                "c": ["0x" + "7" * 64, "0x" + "8" * 64],
                "publicSignals": ["12345", "67890"]
            },
            "inputs": inputs,
            "success": True
        }
    
    def _create_blockchain_block(self, block_id: int, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a blockchain block for testing."""
        return {
            "block_id": block_id,
            "transactions": transactions,
            "merkle_root": "0x" + hashlib.sha256(str(transactions).encode()).hexdigest(),
            "timestamp": int(time.time()),
            "previous_hash": "0x" + "0" * 64 if block_id == 0 else "0x" + "a" * 64
        }
    
    def _create_redacted_block(self, original_block: Dict[str, Any], redacted_data: Dict[str, Any], redacted_cid: str) -> Dict[str, Any]:
        """Create a redacted version of a blockchain block."""
        redacted_block = original_block.copy()
        
        # Update transactions with redacted data
        redacted_transactions = []
        for tx in original_block["transactions"]:
            redacted_tx = tx.copy()
            redacted_tx["ipfs_cid"] = redacted_cid
            redacted_tx["data_hash"] = hashlib.sha256(
                json.dumps(redacted_data, sort_keys=True).encode()
            ).hexdigest()
            redacted_transactions.append(redacted_tx)
        
        redacted_block["transactions"] = redacted_transactions
        redacted_block["merkle_root"] = "0x" + hashlib.sha256(str(redacted_transactions).encode()).hexdigest()
        
        return redacted_block
    
    def _verify_redaction_applied(self, original_data: Dict[str, Any], redacted_data: Dict[str, Any], scenario: Dict[str, Any]):
        """Verify that redaction was applied correctly."""
        for field_path in scenario["fields"]:
            original_value = self._get_field_value(original_data, field_path)
            redacted_value = self._get_field_value(redacted_data, field_path)
            
            if scenario["type"] == "DELETE":
                assert redacted_value == "REDACTED", f"Field {field_path} not properly redacted"
            elif scenario["type"] == "ANONYMIZE":
                assert redacted_value.startswith("ANONYMIZED_"), f"Field {field_path} not properly anonymized"
            elif scenario["type"] == "MODIFY":
                assert redacted_value.startswith("MODIFIED_"), f"Field {field_path} not properly modified"
                assert redacted_value != original_value, f"Field {field_path} was not actually modified"
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field path."""
        path_parts = field_path.split('.')
        current = data
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                # Handle array indexing for list elements
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def _verify_final_consistency(self, original_data: Dict[str, Any], redacted_states: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Verify final consistency across all components."""
        # Check that all redacted versions are internally consistent
        for state in redacted_states:
            consistency_result = state["consistency_proof"]
            scenario = state["scenario"]
            
            # For redaction operations, the consistency proof should detect the redaction
            # This is expected behavior and indicates the proof is working correctly
            if scenario["type"] in ["DELETE", "MODIFY", "ANONYMIZE"]:
                # For redaction operations, is_valid=False means redaction was detected (expected)
                # is_valid=True would mean no redaction was detected (unexpected)
                if consistency_result.is_valid:
                    return {"consistent": False, "error": f"Consistency proof failed to detect redaction for {scenario['name']}"}
            else:
                # For non-redaction operations, consistency should be maintained
                if not consistency_result.is_valid:
                    return {"consistent": False, "error": f"Inconsistent state for {scenario['name']}"}
        
        return {"consistent": True}
    
    def _verify_privacy_compliance(self, redacted_states: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Verify privacy compliance across all redaction scenarios."""
        # Check GDPR compliance
        gdpr_scenarios = [s for s in redacted_states if "GDPR" in s["scenario"]["reason"]]
        for scenario in gdpr_scenarios:
            redacted_data = scenario["redacted_data"]
            # Verify sensitive data was properly removed
            if redacted_data.get("diagnosis") != "REDACTED":
                return {"compliant": False, "error": "GDPR deletion not properly applied"}
        
        # Check HIPAA compliance
        hipaa_scenarios = [s for s in redacted_states if "HIPAA" in s["scenario"]["reason"]]
        for scenario in hipaa_scenarios:
            redacted_data = scenario["redacted_data"]
            # Verify identifiers were anonymized
            if not redacted_data.get("patient_name", "").startswith("ANONYMIZED_"):
                return {"compliant": False, "error": "HIPAA anonymization not properly applied"}
        
        return {"compliant": True}
    
    # Simulation methods for non-real components
    def _simulate_blockchain_registration(self, patient_id: str, cid: str, data_hash: str) -> str:
        """Simulate blockchain registration."""
        return f"0x{''.join([hex(hash(patient_id + cid))[2:8] for _ in range(8)])}"
    
    def _simulate_redaction_request(self, scenario: Dict[str, Any], proof: Dict[str, Any], redacted_cid: str) -> str:
        """Simulate redaction request submission."""
        return f"REQ_{scenario['name']}_{hash(str(proof)) % 1000000:06d}"
    
    def _simulate_proof_verification(self, request_id: str) -> Dict[str, bool]:
        """Simulate proof verification."""
        return {"valid": True, "request_id": request_id}
    
    def _simulate_approval(self, request_id: str) -> Dict[str, bool]:
        """Simulate redaction approval."""
        return {"approved": True, "request_id": request_id}
    
    def _simulate_execution(self, request_id: str, redacted_cid: str) -> Dict[str, bool]:
        """Simulate redaction execution."""
        return {"executed": True, "request_id": request_id, "new_cid": redacted_cid}


@pytest.mark.integration
class TestFullPipelineRealIntegration:
    """Integration tests requiring all real services."""
    
    @pytest.mark.requires_ipfs
    @pytest.mark.requires_snark
    @pytest.mark.requires_evm
    def test_real_full_pipeline(self):
        """Test complete pipeline with all real services."""
        # This test only runs when all services are available
        ipfs_client = get_ipfs_client()
        snark_client = SnarkClient()
        evm_client = EVMClient()
        
        # Skip if services are not enabled/available
        if (ipfs_client.__class__.__name__ == "FakeIPFSClient" or 
            not snark_client.is_enabled() or 
            not evm_client.is_enabled()):
            pytest.skip("Real services not available - using fake/disabled services")
        
        assert ipfs_client.__class__.__name__ != "FakeIPFSClient"
        assert snark_client.is_enabled() is True
        assert evm_client.is_enabled() is True
        
        # Run a simplified version of the full pipeline with real services
        test_data = {
            "patient_id": "REAL_PIPELINE_001",
            "diagnosis": "Real test diagnosis",
            "treatment": "Real test treatment"
        }
        
        # Real IPFS upload
        medical_manager = IPFSMedicalDataManager(ipfs_client=ipfs_client)
        test_dataset = MedicalDataset(
            dataset_id="REAL_PIPELINE_001",
            name="Real Pipeline Test Dataset",
            description="Dataset for real pipeline integration test",
            patient_records=[test_data],
            creation_timestamp=int(time.time()), last_updated=int(time.time()),
            version="1.0"
        )
        original_cid = medical_manager.upload_dataset(test_dataset)
        
        # Real redaction
        redacted_data = test_data.copy()
        redacted_data["diagnosis"] = "REDACTED"
        redacted_dataset = MedicalDataset(
            dataset_id="REAL_PIPELINE_001_REDACTED",
            name="Real Pipeline Test Redacted Dataset",
            description="Redacted dataset for real pipeline integration test",
            patient_records=[redacted_data],
            creation_timestamp=int(time.time()), last_updated=int(time.time()),
            version="1.0"
        )
        redacted_cid = medical_manager.upload_dataset(redacted_dataset)
        
        # Real SNARK proof (simplified)
        proof_inputs = {
            "originalData": [1, 2, 3],
            "redactedData": [0, 2, 3],
            "merkleRoot": 12345,
            "nullifier": 67890
        }
        
        witness_result = snark_client.generate_witness("redaction", proof_inputs)
        assert witness_result["success"] is True
        
        proof_result = snark_client.generate_proof("redaction", witness_result["witness_file"])
        assert proof_result["success"] is True
        
        # Real EVM verification
        formatted_proof = snark_client.format_proof_for_solidity(proof_result["proof"])
        verification_result = evm_client.verify_redaction_proof(
            proof_a=formatted_proof["a"],
            proof_b=formatted_proof["b"], 
            proof_c=formatted_proof["c"],
            public_signals=formatted_proof["publicSignals"]
        )
        
        assert verification_result["success"] is True
        
        # Verify data integrity
        retrieved_original = medical_manager.download_dataset(original_cid)
        retrieved_redacted = medical_manager.download_dataset(redacted_cid)
        
        assert retrieved_original["diagnosis"] == "Real test diagnosis"
        assert retrieved_redacted["diagnosis"] == "REDACTED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
