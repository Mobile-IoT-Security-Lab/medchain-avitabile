#!/usr/bin/env python3
"""
MedChain Quickstart Demo
========================

A minimal, fast demonstration of MedChain's core features.
Perfect for first-time users and quick validation.

Runtime: ~30 seconds
Requirements: None (uses simulated backends)
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from medical.MedicalDataIPFS import IPFSMedicalDataManager, MedicalDatasetGenerator, FakeIPFSClient
from medical.MedicalRedactionEngine import MyRedactionEngine


def quickstart_demo():
    """Run a 5-minute MedChain demonstration."""
    
    print("\n" + "="*60)
    print(" MedChain Quickstart Demo")
    print("="*60)
    print("\nThis demo shows:")
    print("  1. Medical data storage")
    print("  2. SNARK-based redaction")
    print("  3. GDPR compliance")
    print()
    
    # Initialize
    print("Initializing components...")
    ipfs = FakeIPFSClient()
    ipfs_mgr = IPFSMedicalDataManager(ipfs)
    engine = MyRedactionEngine()
    gen = MedicalDatasetGenerator()
    
    # Create small dataset
    print("Creating medical dataset...")
    dataset = gen.generate_dataset(num_patients=5, dataset_name="Quickstart Hospital")
    
    # Upload to IPFS
    print("Uploading to IPFS...")
    ipfs_hash = ipfs_mgr.upload_dataset(dataset)
    print(f"  ✓ Uploaded to IPFS: {ipfs_hash}")
    
    # Store one patient in smart contract
    print("\nStoring patient in smart contract...")
    patient = dataset.patient_records[0]
    record = engine.create_medical_data_record(patient)
    engine.store_medical_data(record)
    print(f"  ✓ Stored patient: {patient['patient_name']}")
    
    # Query data
    print("\nQuerying patient data...")
    retrieved = engine.query_medical_data(patient['patient_id'], "doctor_001")
    if retrieved:
        print(f"  ✓ Found: {retrieved.patient_name}")
        print(f"    Diagnosis: {retrieved.diagnosis}")
    
    # Request DELETE redaction (GDPR)
    print("\nRequesting GDPR data deletion...")
    request_id = engine.request_data_redaction(
        patient_id=patient['patient_id'],
        redaction_type="DELETE",
        reason="GDPR Article 17 - Right to be Forgotten",
        requester="patient_001",
        requester_role="ADMIN"
    )
    print(f"  ✓ Request created: {request_id}")
    
    # Approve (2 approvals needed)
    print("\nApproving redaction...")
    engine.approve_redaction(request_id, "admin_001")
    engine.approve_redaction(request_id, "regulator_001")
    print("  ✓ Approved and executed")
    
    # Verify deletion
    print("\nVerifying deletion...")
    deleted = engine.query_medical_data(patient['patient_id'], "doctor_001")
    if deleted is None:
        print("  ✓ Patient data successfully deleted")
    else:
        print("  ✗ Patient data still exists (unexpected)")
    
    # Show history
    print("\nRedaction history:")
    history = engine.get_redaction_history()
    for entry in history:
        print(f"  - {entry['redaction_type']}: {entry['patient_id']}")
        print(f"    SNARK Proof: {entry['zk_proof_id']}")
    
    print("\n" + "="*60)
    print(" Quickstart Demo Complete! ✓")
    print("="*60)
    print("\nNext steps:")
    print("  - Run full demo: python -m demo.medchain_demo")
    print("  - View docs: cat docs/QUICKSTART.md")
    print("  - Run tests: pytest tests/")
    print()


if __name__ == "__main__":
    quickstart_demo()
