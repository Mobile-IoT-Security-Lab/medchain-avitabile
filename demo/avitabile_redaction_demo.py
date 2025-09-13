#!/usr/bin/env python3
"""
Avitabile Paper Demo: Redaction Workflow
=======================================

Demonstrates the redaction workflow from
"Data Redaction in Smart-Contract-Enabled Permissioned Blockchains":

1) Record onboarding in a contract-backed medical registry
2) Redaction request with SNARK + consistency proofs
3) Multi-party approval reaching policy thresholds
4) Redaction execution and audit trail

Uses the EnhancedRedactionEngine with built-in policy thresholds and proof checks.
"""

import os
import sys
from typing import Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from medical.MedicalRedactionEngine import EnhancedRedactionEngine


def run_avitabile_redaction_demo() -> Tuple[EnhancedRedactionEngine, str, str]:
    print("Avitabile Redaction Workflow Demo")
    print("=" * 35)

    engine = EnhancedRedactionEngine()

    # Onboard two patients (contract-backed storage)
    print("\nOnboarding sample medical records...")
    p1 = engine.create_medical_data_record({
        "patient_id": "AV_PAT_001",
        "patient_name": "Alice Avitabile",
        "medical_record_number": "MRN_AV_1",
        "diagnosis": "Cond X",
        "treatment": "Treat X",
        "physician": "Dr. X",
        "privacy_level": "PRIVATE",
        "consent_status": True,
    })
    p2 = engine.create_medical_data_record({
        "patient_id": "AV_PAT_002",
        "patient_name": "Bob Avitabile",
        "medical_record_number": "MRN_AV_2",
        "diagnosis": "Cond Y",
        "treatment": "Treat Y",
        "physician": "Dr. Y",
        "privacy_level": "CONFIDENTIAL",
        "consent_status": True,
    })
    engine.store_medical_data(p1)
    engine.store_medical_data(p2)

    # Step 1: GDPR DELETE request for patient 1
    print("\nRequesting GDPR DELETE for AV_PAT_001...")
    rid_delete = engine.request_data_redaction(
        patient_id="AV_PAT_001",
        redaction_type="DELETE",
        reason="GDPR Article 17 erasure request",
        requester="regulator_001",
        requester_role="REGULATOR",
    )
    assert rid_delete, "Failed to create DELETE redaction request"
    # Step 2: Approvals (threshold=2 for DELETE)
    engine.approve_redaction(rid_delete, "admin_001", "Compliance approved")
    engine.approve_redaction(rid_delete, "regulator_002", "Second approval")

    # Step 3: HIPAA ANONYMIZE request for patient 2
    print("\nRequesting HIPAA ANONYMIZE for AV_PAT_002...")
    rid_anon = engine.request_data_redaction(
        patient_id="AV_PAT_002",
        redaction_type="ANONYMIZE",
        reason="Research dataset publication",
        requester="researcher_001",
        requester_role="RESEARCHER",
    )
    assert rid_anon, "Failed to create ANONYMIZE redaction request"
    # Step 4: Approvals (threshold=3 for ANONYMIZE)
    engine.approve_redaction(rid_anon, "admin_001", "Research policy approved")
    engine.approve_redaction(rid_anon, "regulator_001", "Privacy review")
    engine.approve_redaction(rid_anon, "ethics_board", "Ethics approval")

    # Verify outcomes
    print("\nVerifying outcomes...")
    rec1 = engine.query_medical_data("AV_PAT_001", "auditor")
    assert rec1 is None, "Patient AV_PAT_001 should be deleted"

    rec2 = engine.query_medical_data("AV_PAT_002", "auditor")
    assert rec2 is not None, "Patient AV_PAT_002 should exist"
    # Object or dict record
    name = rec2.patient_name if hasattr(rec2, "patient_name") else rec2["patient_name"]
    assert name == "[REDACTED]", "Patient AV_PAT_002 should be anonymized"

    # Audit trail
    history = engine.get_redaction_history()
    print(f"Redactions executed: {len(history)}")
    for h in history:
        print(f"  - {h['request_id']} [{h['redaction_type']}] for {h['patient_id']}")

    print("\nAvitabile redaction flow demo completed successfully.")
    return engine, rid_delete, rid_anon


if __name__ == "__main__":
    run_avitabile_redaction_demo()
