#!/usr/bin/env python3
"""
Avitabile Paper Demo: Consistency Proofs (Contract State)
========================================================

Shows a simplified proof-of-consistency check for contract state redaction:
- Pre-state: medical record present
- Post-state: record anonymized
- Verifier checks that only allowed fields changed and others remained equal

This reflects the paper's requirement that after redaction, global state
remains consistent with policy and integrity constraints.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ZK.ProofOfConsistency import ConsistencyProofGenerator, ConsistencyCheckType


def run_avitabile_consistency_demo():
    print("Avitabile Consistency Proof Demo (Contract State)")
    print("=" * 55)

    gen = ConsistencyProofGenerator()

    # Pre-state: one patient record
    pre_state = {
        "contract_states": {
            "0xMED": {
                "patient_id": "PAT_X",
                "patient_name": "John X",
                "medical_record_number": "MRN_X",
                "diagnosis": "Cond X",
                "treatment": "Treat X",
                "physician": "Dr. X",
            }
        }
    }

    # Post-state: anonymized sensitive identifiers (as allowed by policy)
    post_state = {
        "contract_states": {
            "0xMED": {
                "patient_id": "PAT_X",
                "patient_name": "[REDACTED]",
                "medical_record_number": "[REDACTED]",
                "diagnosis": "Cond X",
                "treatment": "Treat X",
                "physician": "[REDACTED]",
            }
        }
    }

    operation = {
        "type": "REDACT_CONTRACT_DATA",
        "redaction_type": "ANONYMIZE",
        "redacted_fields": ["patient_name", "medical_record_number", "physician"],
        "affected_contracts": ["0xMED"],
    }

    proof = gen.generate_consistency_proof(
        check_type=ConsistencyCheckType.SMART_CONTRACT_STATE,
        pre_redaction_data=pre_state,
        post_redaction_data=post_state,
        operation_details=operation,
    )

    ok = proof.is_valid
    print(f"Consistency verification passed: {ok}")
    assert ok, "Consistency verification should pass for valid anonymization"
    print("Demo complete: contract state remains consistent under allowed redaction.")


if __name__ == "__main__":
    run_avitabile_consistency_demo()
