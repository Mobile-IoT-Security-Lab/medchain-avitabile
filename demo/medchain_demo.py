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

# Ensure project root is importable when running via path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from medical.MedicalDataIPFS import IPFSMedicalDataManager, MedicalDatasetGenerator, FakeIPFSClient
from medical.MedicalRedactionEngine import MyRedactionEngine
from ZK.SNARKs import RedactionSNARKManager
from ZK.ProofOfConsistency import ConsistencyProofGenerator
from adapters.ipfs import get_ipfs_client
from adapters.evm import get_evm_client
from adapters.config import env_str


class MedChainDemo:
    """Complete MedChain demonstration."""
    
    def __init__(self):
        print(" Initializing MedChain Demo System")
        print("=" * 50)
        
        # Initialize components
        # Prefer real IPFS client if enabled and reachable; fallback to Fake
        self.ipfs_client = get_ipfs_client() or FakeIPFSClient()
        self.ipfs_manager = IPFSMedicalDataManager(self.ipfs_client)
        self.redaction_engine = MyRedactionEngine()
        self.dataset_generator = MedicalDatasetGenerator()
        self.snark_manager = RedactionSNARKManager()
        self.consistency_generator = ConsistencyProofGenerator()

        # Try to initialize EVM backend (optional)
        self.evm = get_evm_client()
        self.evm_manager = None
        self.evm_enabled = False
        if self.evm is not None:
            # Try load existing address from env or deployments
            addr = env_str("MEDICAL_CONTRACT_ADDRESS")
            loaded = None
            if addr:
                loaded = self.evm.load_contract("MedicalDataManager", addr)
            else:
                loaded = self.evm.load_contract("MedicalDataManager")
            if loaded is not None:
                self.evm_manager = loaded
                self.evm_enabled = True
                # Attach EVM backend to engine if requested
                try:
                    if env_str("REDACTION_BACKEND", "SIMULATED").strip().upper() == "EVM":
                        # Attach only if engine exposes method
                        attach = getattr(self.redaction_engine, "attach_evm_backend", None)
                        if callable(attach):
                            attach(self.evm_manager, self.ipfs_manager)
                except Exception:
                    pass
            else:
                # Best-effort deploy if artifacts present
                deployed = self.evm.deploy("MedicalDataManager")
                if deployed:
                    mgr_addr, mgr = deployed
                    print(f" Deployed MedicalDataManager at {mgr_addr}")
                    self.evm_manager = mgr
                    self.evm_enabled = True
                    try:
                        if env_str("REDACTION_BACKEND", "SIMULATED").strip().upper() == "EVM":
                            attach = getattr(self.redaction_engine, "attach_evm_backend", None)
                            if callable(attach):
                                attach(self.evm_manager, self.ipfs_manager)
                    except Exception:
                        pass
        
        # Demo state
        self.demo_datasets = []
        self.demo_patients = []
        self.demo_redactions = []
        
        print(" All components initialized successfully")
        
    def run_complete_demo(self):
        """Run the complete MedChain demonstration."""
        
        print("\n Starting MedChain Complete Demonstration")
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
            
            print("\n MedChain Demo Completed Successfully!")
            self.print_final_summary()
            
        except Exception as e:
            print(f"\n Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    # The remainder of the class is identical to the original demo script.
    # Copied from the original demo_medchain.py
    def phase1_create_and_upload_dataset(self):
        print("\n Phase 1: Creating Medical Dataset and IPFS Upload")
        print("-" * 50)
        print("Generating comprehensive medical dataset...")
        dataset = self.dataset_generator.generate_dataset(
            num_patients=100,
            dataset_name="MedChain Hospital Emergency Records"
        )
        print(f" Created dataset '{dataset.name}' with {len(dataset.patient_records)} patients")
        print(f"   Dataset ID: {dataset.dataset_id}")
        print("\\nUploading dataset to IPFS...")
        ipfs_hash = self.ipfs_manager.upload_dataset(dataset, encrypt=True)
        if ipfs_hash:
            print(f" Dataset uploaded successfully")
            print(f"   IPFS Hash: {ipfs_hash}")
            print(f"   Size: {self.ipfs_client.stat(ipfs_hash)['size']} bytes")
            self.demo_datasets.append(dataset)
            self.demo_patients = dataset.patient_records[:10]

    def phase2_blockchain_integration(self):
        print("\n Phase 2: Blockchain Integration with Smart Contracts")
        print("-" * 50)
        print("Storing selected patients in smart contract...")
        for p in self.demo_patients:
            record = self.redaction_engine.create_medical_data_record(p)
            self.redaction_engine.store_medical_data(record)
            # If EVM backend is enabled, publish pointer to on-chain manager
            if self.evm_enabled and self.evm_manager is not None and hasattr(self.demo_datasets[0], 'ipfs_hash'):
                pid = p["patient_id"]
                ipfs_hash = self.demo_datasets[0].ipfs_hash or ""
                if ipfs_hash:
                    # Resolve ciphertext hash from dataset registry (hex to bytes32)
                    try:
                        ds = self.demo_datasets[0]
                        meta = self.ipfs_manager.dataset_registry.get(ds.dataset_id, {})
                        ct_hex = meta.get("ciphertext_hash_hex") or ""
                        if ct_hex:
                            ct_b = bytes.fromhex(ct_hex)
                        else:
                            # Fallback: compute over stored envelope payload fetched via IPFS
                            content = self.ipfs_client.get(ipfs_hash) or ""
                            import hashlib
                            ct_b = bytes.fromhex(hashlib.sha256(content.encode()).hexdigest())
                        txh = self.evm.storeMedicalData(self.evm_manager, pid, ipfs_hash, ct_b)
                    except Exception as e:
                        txh = None
                    if txh:
                        print(f"  On-chain storeMedicalData tx: {txh}")
        print(f" Stored {len(self.demo_patients)} patient records (simulated); EVM pointers set: {self.evm_enabled}")

    def phase3_query_and_access_control(self):
        print("\n Phase 3: Query and Access Control")
        print("-" * 50)
        pid = self.demo_patients[0]["patient_id"]
        rec = self.redaction_engine.query_medical_data(pid, "researcher_001")
        if rec:
            print(f" Queried patient {pid}: {rec.patient_name if hasattr(rec,'patient_name') else rec['patient_name']}")

    def phase4_gdpr_right_to_be_forgotten(self):
        print("\n Phase 4: GDPR Right to be Forgotten")
        print("-" * 50)
        pid = self.demo_patients[1]["patient_id"]
        rid = self.redaction_engine.request_data_redaction(
            patient_id=pid,
            redaction_type="DELETE",
            reason="GDPR Article 17 request",
            requester="regulator_001",
            requester_role="REGULATOR",
        )
        if rid:
            self.redaction_engine.approve_redaction(rid, "admin_001")
            self.redaction_engine.approve_redaction(rid, "regulator_002")
            self.demo_redactions.append(rid)
            # Also log an on-chain redaction request event (optional)
            if self.evm_enabled and self.evm_manager is not None:
                # Try with proof path using verifier stub. Build inputs from simulated engine.
                # Compute simple public inputs as SHA-256 digests.
                try:
                    record = self.redaction_engine.medical_contract.state["medical_records"].get(pid)
                    if record and hasattr(record, "__dict__"):
                        import json, hashlib
                        original_json = json.dumps(record.__dict__, sort_keys=True)
                        redacted_json = self.redaction_engine._generate_redacted_data(record, "DELETE")
                        original_hash = bytes.fromhex(hashlib.sha256(original_json.encode()).hexdigest())
                        redacted_hash = bytes.fromhex(hashlib.sha256(redacted_json.encode()).hexdigest())
                        policy_hex = self.redaction_engine._get_applicable_policy_hash("DELETE")
                        policy_hash = bytes.fromhex(policy_hex)
                        merkle_root = bytes.fromhex(hashlib.sha256(b"medical_contract_root").hexdigest())
                        proof = b""  # verifier stub always true
                        txh2 = self.evm.requestDataRedactionWithProof(
                            self.evm_manager, pid, "DELETE", "GDPR Article 17 request",
                            proof, policy_hash, merkle_root, original_hash, redacted_hash
                        )
                        if txh2:
                            print(f"  On-chain requestDataRedactionWithProof tx: {txh2}")
                    else:
                        # Fallback without proof
                        txh = self.evm.requestDataRedaction(self.evm_manager, pid, "DELETE", "GDPR Article 17 request")
                        if txh:
                            print(f"  On-chain requestDataRedaction tx: {txh}")
                except Exception as e:
                    print(f"  Skipped on-chain proof call: {e}")

    def phase5_snark_and_consistency_verification(self):
        print("\n Phase 5: SNARK Proofs and Consistency Verification")
        print("-" * 50)
        print(" SNARK + consistency already verified during approvals")

    def phase6_audit_and_compliance(self):
        print("\n Phase 6: Audit and Compliance")
        print("-" * 50)
        history = self.redaction_engine.get_redaction_history()
        print(f" Redactions executed: {len(history)}")
        # Query on-chain events if enabled
        if self.evm_enabled and self.evm_manager is not None:
            try:
                ds_logs = self.evm.get_events(self.evm_manager, "DataStored")
                rr_logs = self.evm.get_events(self.evm_manager, "RedactionRequested")
                print(f" On-chain DataStored events: {len(ds_logs)}")
                print(f" On-chain RedactionRequested events: {len(rr_logs)}")
            except Exception as e:
                print(f" Failed to query on-chain events: {e}")

    def phase7_advanced_redaction_scenarios(self):
        print("\n Phase 7: Advanced Scenarios")
        print("-" * 50)
        pid = self.demo_patients[2]["patient_id"]
        rid = self.redaction_engine.request_data_redaction(
            patient_id=pid,
            redaction_type="ANONYMIZE",
            reason="Clinical study data anonymization",
            requester="researcher_001",
            requester_role="RESEARCHER",
        )
        if rid:
            self.redaction_engine.approve_redaction(rid, "admin_001")
            self.redaction_engine.approve_redaction(rid, "regulator_001")
            self.redaction_engine.approve_redaction(rid, "ethics_board")
            self.demo_redactions.append(rid)

    def print_final_summary(self):
        print("\n MedChain Demo Summary Report")
        print("=" * 50)
        print(f" Datasets created: {len(self.demo_datasets)}")
        print(f" Patients demoed: {len(self.demo_patients)}")
        print(f" Redactions executed: {len(self.redaction_engine.get_redaction_history())}")


if __name__ == "__main__":
    demo = MedChainDemo()
    demo.run_complete_demo()
