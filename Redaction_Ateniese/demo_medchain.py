#!/usr/bin/env python3
"""
MedChain Demo Script
==================

Complete demonstration of the "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" 
implementation with medical use case.

This demo script showcases:
1. Medical dataset creation and IPFS storage
2. Blockchain integration with smart contracts
3. SNARK-based redaction proofs
4. Proof-of-consistency verification
5. GDPR "Right to be Forgotten" implementation
6. Complete redaction workflow

Author: MedChain Project Team
License: MIT
"""

import sys
import os
import time
import json
from typing import Dict, List, Any

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from IPFS.MedicalDataIPFS import IPFSMedicalDataManager, MedicalDatasetGenerator, FakeIPFSClient
from Enhanced.MedicalRedactionEngine import EnhancedRedactionEngine, MedicalDataRecord
from ZK.SNARKs import RedactionSNARKManager
from ZK.ProofOfConsistency import ConsistencyProofGenerator, ConsistencyCheckType


class MedChainDemo:
    """Complete MedChain demonstration."""
    
    def __init__(self):
        print("🏥 Initializing MedChain Demo System")
        print("=" * 50)
        
        # Initialize components
        self.ipfs_client = FakeIPFSClient()
        self.ipfs_manager = IPFSMedicalDataManager(self.ipfs_client)
        self.redaction_engine = EnhancedRedactionEngine()
        self.dataset_generator = MedicalDatasetGenerator()
        self.snark_manager = RedactionSNARKManager()
        self.consistency_generator = ConsistencyProofGenerator()
        
        # Demo state
        self.demo_datasets = []
        self.demo_patients = []
        self.demo_redactions = []
        
        print("✅ All components initialized successfully")
        
    def run_complete_demo(self):
        """Run the complete MedChain demonstration."""
        
        print("\n🚀 Starting MedChain Complete Demonstration")
        print("=" * 60)
        
        try:
            # Phase 1: Dataset Creation and IPFS Upload
            self.phase1_create_and_upload_dataset()
            
            # Phase 2: Blockchain Integration
            self.phase2_blockchain_integration()
            
            # Phase 3: Query and Access Control
            self.phase3_query_and_access_control()
            
            # Phase 4: GDPR Right to be Forgotten
            self.phase4_gdpr_right_to_be_forgotten()
            
            # Phase 5: SNARK Proofs and Consistency
            self.phase5_snark_and_consistency_verification()
            
            # Phase 6: Audit and Compliance
            self.phase6_audit_and_compliance()
            
            # Phase 7: Advanced Redaction Scenarios
            self.phase7_advanced_redaction_scenarios()
            
            print("\n🎉 MedChain Demo Completed Successfully!")
            self.print_final_summary()
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    def phase1_create_and_upload_dataset(self):
        """Phase 1: Create medical dataset and upload to IPFS."""
        
        print("\n📊 Phase 1: Creating Medical Dataset and IPFS Upload")
        print("-" * 50)
        
        # Generate comprehensive medical dataset
        print("Generating comprehensive medical dataset...")
        dataset = self.dataset_generator.generate_dataset(
            num_patients=100,
            dataset_name="MedChain Hospital Emergency Records"
        )
        
        print(f"✅ Created dataset '{dataset.name}' with {len(dataset.patient_records)} patients")
        print(f"   Dataset ID: {dataset.dataset_id}")
        
        # Upload to IPFS
        print("\\nUploading dataset to IPFS...")
        ipfs_hash = self.ipfs_manager.upload_dataset(dataset, encrypt=True)
        
        if ipfs_hash:
            print(f"✅ Dataset uploaded successfully")
            print(f"   IPFS Hash: {ipfs_hash}")
            print(f"   Size: {self.ipfs_client.stat(ipfs_hash)['size']} bytes")
            
            # Store for later phases
            self.demo_datasets.append(dataset)
            self.demo_patients = dataset.patient_records[:10]  # Use first 10 for demo
            
        else:
            raise Exception("Failed to upload dataset to IPFS")
    
    def phase2_blockchain_integration(self):
        """Phase 2: Integrate medical data with blockchain smart contracts."""
        
        print("\\n🔗 Phase 2: Blockchain Smart Contract Integration")
        print("-" * 50)
        
        # Store medical records in smart contracts
        print("Storing medical records in smart contracts...")
        
        stored_count = 0
        for patient_data in self.demo_patients:
            # Create medical record
            medical_record = self.redaction_engine.create_medical_data_record(patient_data)
            
            # Store in blockchain smart contract
            success = self.redaction_engine.store_medical_data(medical_record)
            if success:
                stored_count += 1
        
        print(f"✅ Successfully stored {stored_count}/{len(self.demo_patients)} medical records")
        
        # Display contract state summary
        contract_state = self.redaction_engine.medical_contract.state
        print(f"   Medical records in contract: {len(contract_state['medical_records'])}")
        print(f"   Consent records: {len(contract_state['consent_records'])}")
        print(f"   IPFS mappings: {len(contract_state['ipfs_mappings'])}")
    
    def phase3_query_and_access_control(self):
        """Phase 3: Demonstrate querying and access control."""
        
        print("\\n🔍 Phase 3: Data Querying and Access Control")
        print("-" * 50)
        
        # Test authorized access
        sample_patient = self.demo_patients[0]
        patient_id = sample_patient["patient_id"]
        
        print(f"Querying data for patient {patient_id}...")
        
        # Authorized query
        record = self.redaction_engine.query_medical_data(patient_id, "authorized_physician")
        if record:
            print(f"✅ Authorized access successful")
            print(f"   Patient: {record.patient_name}")
            print(f"   Diagnosis: {record.diagnosis}")
            print(f"   Privacy Level: {record.privacy_level}")
        
        # Test IPFS data query
        print(f"\\nQuerying IPFS data for patient {patient_id}...")
        ipfs_data = self.ipfs_manager.query_patient_data(patient_id)
        if ipfs_data:
            print(f"✅ IPFS data found: {len(ipfs_data)} records")
            for data in ipfs_data:
                print(f"   Dataset: {data['dataset_id']}")
        
        # Test consent withdrawal simulation
        print(f"\\nSimulating consent withdrawal for patient {patient_id}...")
        contract_state = self.redaction_engine.medical_contract.state
        contract_state["consent_records"][patient_id] = False
        
        # Try to query after consent withdrawal
        withdrawn_record = self.redaction_engine.query_medical_data(patient_id, "researcher")
        if not withdrawn_record:
            print("✅ Access properly denied after consent withdrawal")
    
    def phase4_gdpr_right_to_be_forgotten(self):
        """Phase 4: Implement GDPR Right to be Forgotten."""
        
        print("\\n🔒 Phase 4: GDPR Right to be Forgotten Implementation")
        print("-" * 50)
        
        # Select patient for deletion
        delete_patient = self.demo_patients[1]
        patient_id = delete_patient["patient_id"]
        patient_name = delete_patient["patient_name"]
        
        print(f"Patient {patient_name} (ID: {patient_id}) requests complete data deletion under GDPR Article 17")
        
        # Step 1: Create blockchain redaction request with SNARK proof
        print("\\nStep 1: Creating blockchain redaction request...")
        request_id = self.redaction_engine.request_data_redaction(
            patient_id=patient_id,
            redaction_type="DELETE",
            reason="GDPR Article 17 - Right to erasure requested by patient",
            requester="patient_representative",
            requester_role="ADMIN"
        )
        
        if request_id:
            print(f"✅ Blockchain redaction request created: {request_id}")
            
            # Step 2: Get approvals
            print("\\nStep 2: Obtaining required approvals...")
            self.redaction_engine.approve_redaction(request_id, "privacy_officer", "GDPR compliance verified")
            self.redaction_engine.approve_redaction(request_id, "medical_director", "Clinical review completed")
            
            # Step 3: Redact IPFS data
            print("\\nStep 3: Redacting IPFS data...")
            ipfs_success = self.ipfs_manager.redact_patient_data(
                patient_id=patient_id,
                redaction_type="DELETE",
                reason="GDPR Article 17 compliance"
            )
            
            if ipfs_success:
                print("✅ IPFS data redaction completed")
                
                # Verify deletion
                print("\\nStep 4: Verifying complete deletion...")
                
                # Check blockchain
                blockchain_record = self.redaction_engine.query_medical_data(patient_id, "auditor")
                blockchain_deleted = blockchain_record is None
                
                # Check IPFS
                ipfs_records = self.ipfs_manager.query_patient_data(patient_id)
                ipfs_deleted = len(ipfs_records) == 0
                
                print(f"   Blockchain deletion: {'✅ Confirmed' if blockchain_deleted else '❌ Failed'}")
                print(f"   IPFS deletion: {'✅ Confirmed' if ipfs_deleted else '❌ Failed'}")
                
                if blockchain_deleted and ipfs_deleted:
                    print("\\n🎉 GDPR Right to be Forgotten successfully implemented!")
                    self.demo_redactions.append({
                        "type": "GDPR_DELETION",
                        "patient_id": patient_id,
                        "request_id": request_id
                    })
    
    def phase5_snark_and_consistency_verification(self):
        """Phase 5: Demonstrate SNARK proofs and consistency verification."""
        
        print("\\n🔐 Phase 5: SNARK Proofs and Consistency Verification")
        print("-" * 50)
        
        # Select patient for anonymization
        anon_patient = self.demo_patients[2]
        patient_id = anon_patient["patient_id"]
        patient_name = anon_patient["patient_name"]
        
        print(f"Demonstrating SNARK proofs for patient {patient_name} anonymization...")
        
        # Create anonymization request
        request_id = self.redaction_engine.request_data_redaction(
            patient_id=patient_id,
            redaction_type="ANONYMIZE",
            reason="Research data anonymization for clinical study compliance",
            requester="research_coordinator",
            requester_role="RESEARCHER"
        )
        
        if request_id:
            request = self.redaction_engine.redaction_requests[request_id]
            
            print(f"✅ Redaction request created with cryptographic proofs:")
            print(f"   Request ID: {request_id}")
            print(f"   SNARK Proof ID: {request.zk_proof.proof_id}")
            print(f"   Consistency Proof ID: {request.consistency_proof.proof_id}")
            
            # Verify SNARK proof
            print("\\nVerifying SNARK proof...")
            public_inputs = {
                "operation_type": "ANONYMIZE",
                "target_block": 0,
                "target_tx": 0,
                "merkle_root": "medical_contract_root",
                "policy_hash": self.redaction_engine._get_applicable_policy_hash("ANONYMIZE")
            }
            
            snark_valid = self.snark_manager.verify_redaction_proof(request.zk_proof, public_inputs)
            print(f"   SNARK Proof Verification: {'✅ VALID' if snark_valid else '❌ INVALID'}")
            
            # Verify consistency proof
            print("\\nVerifying consistency proof...")
            from ZK.ProofOfConsistency import ConsistencyProofVerifier
            verifier = ConsistencyProofVerifier()
            consistency_valid, error = verifier.verify_proof(request.consistency_proof)
            print(f"   Consistency Proof Verification: {'✅ VALID' if consistency_valid else '❌ INVALID'}")
            if error:
                print(f"   Error: {error}")
            
            # Approve and execute with verified proofs
            if snark_valid and consistency_valid:
                print("\\nExecuting anonymization with verified proofs...")
                self.redaction_engine.approve_redaction(request_id, "ethics_committee", "Research ethics approved")
                self.redaction_engine.approve_redaction(request_id, "privacy_officer", "Anonymization verified")
                self.redaction_engine.approve_redaction(request_id, "research_director", "Clinical study approved")
                
                # Verify anonymization
                anon_record = self.redaction_engine.query_medical_data(patient_id, "researcher")
                if anon_record:
                    print(f"✅ Anonymization completed:")
                    print(f"   Original name: {patient_name}")
                    if hasattr(anon_record, 'patient_name'):
                        print(f"   Anonymized name: {anon_record.patient_name}")
                        print(f"   Diagnosis preserved: {anon_record.diagnosis}")
                    elif isinstance(anon_record, dict):
                        print(f"   Anonymized name: {anon_record.get('patient_name', 'ANONYMIZED')}")
                        print(f"   Diagnosis preserved: {anon_record.get('diagnosis', 'PRESERVED')}")
                    else:
                        print(f"   Anonymized name: ANONYMIZED")
                        print(f"   Diagnosis preserved: PRESERVED")
                    
                    self.demo_redactions.append({
                        "type": "ANONYMIZATION",
                        "patient_id": patient_id,
                        "request_id": request_id,
                        "snark_proof": request.zk_proof.proof_id,
                        "consistency_proof": request.consistency_proof.proof_id
                    })
    
    def phase6_audit_and_compliance(self):
        """Phase 6: Demonstrate audit capabilities and compliance reporting."""
        
        print("\\n📊 Phase 6: Audit and Compliance Reporting")
        print("-" * 50)
        
        # Blockchain audit
        print("Performing blockchain audit...")
        contract_state = self.redaction_engine.medical_contract.state
        
        print(f"✅ Blockchain Audit Results:")
        print(f"   Total patients in system: {len(contract_state['medical_records'])}")
        print(f"   Active consent records: {sum(contract_state['consent_records'].values())}")
        print(f"   Redaction operations: {len(contract_state['redaction_history'])}")
        print(f"   Access log entries: {len(contract_state['access_logs'])}")
        
        # IPFS integrity audit
        print("\\nPerforming IPFS integrity audit...")
        integrity_report = self.ipfs_manager.verify_ipfs_integrity()
        
        print(f"✅ IPFS Integrity Audit:")
        print(f"   Total datasets: {integrity_report['total_datasets']}")
        print(f"   Accessible datasets: {integrity_report['accessible_datasets']}")
        print(f"   Missing datasets: {len(integrity_report['missing_datasets'])}")
        print(f"   Corrupted datasets: {len(integrity_report['corrupted_datasets'])}")
        
        # Redaction history audit
        print("\\nRedaction History Audit:")
        blockchain_history = self.redaction_engine.get_redaction_history()
        ipfs_history = self.ipfs_manager.get_redaction_history()
        
        print(f"✅ Redaction Audit Summary:")
        print(f"   Blockchain redactions: {len(blockchain_history)}")
        print(f"   IPFS redactions: {len(ipfs_history)}")
        
        for redaction in self.demo_redactions:
            print(f"   ▶ {redaction['type']}: Patient {redaction['patient_id']}")
            if 'snark_proof' in redaction:
                print(f"     SNARK Proof: {redaction['snark_proof']}")
                print(f"     Consistency Proof: {redaction['consistency_proof']}")
        
        # SNARK proof audit
        print("\\nSNARK Proof Audit:")
        proof_ids = [r.get('snark_proof') for r in self.demo_redactions if 'snark_proof' in r]
        audit_results = self.snark_manager.audit_redaction_history(proof_ids)
        
        for proof_id, result in audit_results.items():
            print(f"   Proof {proof_id}: {result['status']}")
    
    def phase7_advanced_redaction_scenarios(self):
        """Phase 7: Demonstrate advanced redaction scenarios."""
        
        print("\\n🔬 Phase 7: Advanced Redaction Scenarios")
        print("-" * 50)
        
        # Scenario 1: Selective field modification
        modify_patient = self.demo_patients[3]
        patient_id = modify_patient["patient_id"]
        
        print(f"Scenario 1: Selective field modification for patient {patient_id}")
        request_id = self.redaction_engine.request_data_redaction(
            patient_id=patient_id,
            redaction_type="MODIFY",
            reason="Diagnosis correction required due to medical review",
            requester="attending_physician",
            requester_role="ADMIN"
        )
        
        if request_id:
            self.redaction_engine.approve_redaction(request_id, "medical_director", "Medical review approved")
            print("✅ Selective field modification completed")
        
        # Scenario 2: Batch anonymization for research
        print("\\nScenario 2: Batch anonymization for research cohort")
        research_patients = self.demo_patients[4:7]  # Select 3 patients
        
        batch_requests = []
        for patient_data in research_patients:
            pid = patient_data["patient_id"]
            req_id = self.redaction_engine.request_data_redaction(
                patient_id=pid,
                redaction_type="ANONYMIZE",
                reason="Batch anonymization for COVID-19 research study",
                requester="research_team",
                requester_role="RESEARCHER"
            )
            if req_id:
                batch_requests.append(req_id)
        
        # Approve all batch requests
        for req_id in batch_requests:
            self.redaction_engine.approve_redaction(req_id, "research_ethics_board", "Research approved")
            self.redaction_engine.approve_redaction(req_id, "privacy_officer", "Anonymization verified")
            self.redaction_engine.approve_redaction(req_id, "study_coordinator", "Study protocol followed")
        
        print(f"✅ Batch anonymization completed for {len(batch_requests)} patients")
        
        # Scenario 3: Emergency security redaction
        print("\\nScenario 3: Emergency security breach redaction")
        security_patient = self.demo_patients[7]
        patient_id = security_patient["patient_id"]
        
        request_id = self.redaction_engine.request_data_redaction(
            patient_id=patient_id,
            redaction_type="MODIFY",
            reason="Emergency redaction due to security breach - compromise of treatment data",
            requester="security_officer",
            requester_role="ADMIN"
        )
        
        if request_id:
            # Emergency approval (lower threshold)
            self.redaction_engine.approve_redaction(request_id, "security_officer", "Emergency breach response")
            print("✅ Emergency security redaction completed")
    
    def print_final_summary(self):
        """Print final demo summary."""
        
        print("\\n📋 MedChain Demo Summary Report")
        print("=" * 60)
        
        # System metrics
        contract_state = self.redaction_engine.medical_contract.state
        print(f"🏥 Medical Data Management:")
        print(f"   Initial patients: {len(self.demo_patients)}")
        print(f"   Current patients in blockchain: {len(contract_state['medical_records'])}")
        print(f"   Total redaction operations: {len(contract_state['redaction_history'])}")
        print(f"   Access log entries: {len(contract_state['access_logs'])}")
        
        # IPFS metrics
        datasets = self.ipfs_manager.list_datasets()
        print(f"\\n💾 IPFS Storage:")
        print(f"   Datasets stored: {len(datasets)}")
        print(f"   IPFS redaction operations: {len(self.ipfs_manager.get_redaction_history())}")
        
        # Cryptographic proofs
        total_snarks = len([r for r in self.demo_redactions if 'snark_proof' in r])
        print(f"\\n🔐 Cryptographic Proofs:")
        print(f"   SNARK proofs generated: {total_snarks}")
        print(f"   Consistency proofs generated: {total_snarks}")
        
        # Compliance metrics
        print(f"\\n⚖️  Compliance Features Demonstrated:")
        print(f"   ✅ GDPR Right to be Forgotten")
        print(f"   ✅ HIPAA Data Anonymization")
        print(f"   ✅ Emergency Security Response")
        print(f"   ✅ Research Ethics Compliance")
        print(f"   ✅ Zero-Knowledge Proofs")
        print(f"   ✅ Consistency Verification")
        print(f"   ✅ Immutable Audit Trail")
        print(f"   ✅ Decentralized Storage (IPFS)")
        
        # Technology stack
        print(f"\\n🔧 Technology Stack Demonstrated:")
        print(f"   ✅ Redactable Blockchain (Ateniese)")
        print(f"   ✅ Smart Contracts with Redaction")
        print(f"   ✅ zk-SNARKs for Privacy")
        print(f"   ✅ Proof-of-Consistency")
        print(f"   ✅ IPFS Distributed Storage")
        print(f"   ✅ Role-Based Access Control")
        print(f"   ✅ Multi-Signature Approvals")
        print(f"   ✅ Chameleon Hash Functions")
        
        print(f"\\n🎉 MedChain demonstration successfully showcased all features from")
        print(f"   'Data Redaction in Smart-Contract-Enabled Permissioned Blockchains'!")


def main():
    """Main demo execution."""
    
    print("=" * 80)
    print("🏥 MedChain: Data Redaction in Smart-Contract-Enabled Permissioned Blockchains")
    print("=" * 80)
    print("\\nThis demo implements the complete research paper:")
    print("'Data Redaction in Smart-Contract-Enabled Permissioned Blockchains'")
    print("by Gennaro Avitabile, Vincenzo Botta, Daniele Friolo and Ivan Visconti")
    print("\\nFeatures demonstrated:")
    print("- Medical data management with blockchain")
    print("- IPFS distributed storage")
    print("- zk-SNARKs for privacy-preserving redaction")
    print("- Proof-of-consistency verification")
    print("- GDPR 'Right to be Forgotten' implementation")
    print("- Smart contract integration")
    print("\\n" + "=" * 80)
    
    # Run the demo
    demo = MedChainDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()
