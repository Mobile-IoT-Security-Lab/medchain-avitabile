#!/usr/bin/env python3
"""
Quiet test for MyRedactionEngine ensuring no exceptions and correct final states.
"""
import sys, os, unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medical.MedicalRedactionEngine import MyRedactionEngine

class TestMedicalRedactionQuiet(unittest.TestCase):
    def setUp(self):
        self.engine = MyRedactionEngine()
        # Seed two patients
        p1 = {
            "patient_id": "Q_PAT_001",
            "patient_name": "Alice",
            "medical_record_number": "MRN_Q1",
            "diagnosis": "Cond A",
            "treatment": "Treat A",
            "physician": "Dr. A",
            "privacy_level": "PRIVATE",
            "consent_status": True,
        }
        p2 = {
            "patient_id": "Q_PAT_002",
            "patient_name": "Bob",
            "medical_record_number": "MRN_Q2",
            "diagnosis": "Cond B",
            "treatment": "Treat B",
            "physician": "Dr. B",
            "privacy_level": "PRIVATE",
            "consent_status": True,
        }
        self.engine.store_medical_data(self.engine.create_medical_data_record(p1))
        self.engine.store_medical_data(self.engine.create_medical_data_record(p2))

    def test_delete_and_anonymize(self):
        # Request DELETE for Q_PAT_001
        rid_del = self.engine.request_data_redaction(
            patient_id="Q_PAT_001",
            redaction_type="DELETE",
            reason="GDPR Article 17",
            requester="reg_1",
            requester_role="REGULATOR",
        )
        self.assertIsNotNone(rid_del)
        # Approvals (threshold=2)
        self.assertTrue(self.engine.approve_redaction(rid_del, "admin_1"))
        # Second approval triggers execution
        self.assertTrue(self.engine.approve_redaction(rid_del, "reg_2"))

        # Request ANONYMIZE for Q_PAT_002
        rid_anon = self.engine.request_data_redaction(
            patient_id="Q_PAT_002",
            redaction_type="ANONYMIZE",
            reason="Research anonymization",
            requester="res_1",
            requester_role="RESEARCHER",
        )
        self.assertIsNotNone(rid_anon)
        # Approvals (threshold=3)
        self.assertTrue(self.engine.approve_redaction(rid_anon, "admin_1"))
        self.assertTrue(self.engine.approve_redaction(rid_anon, "reg_1"))
        self.assertTrue(self.engine.approve_redaction(rid_anon, "ethics_board"))

        # Validate final state
        state = self.engine.medical_contract.state
        self.assertNotIn("Q_PAT_001", state["medical_records"])  # deleted
        self.assertNotIn("Q_PAT_001", state["consent_records"])   # deleted

        rec2 = state["medical_records"]["Q_PAT_002"]
        # Handle object/dict storage
        if hasattr(rec2, "__dict__"):
            self.assertEqual(rec2.patient_name, "[REDACTED]")
            self.assertEqual(rec2.medical_record_number, "[REDACTED]")
            self.assertEqual(rec2.physician, "[REDACTED]")
        else:
            self.assertEqual(rec2["patient_name"], "[REDACTED]")
            self.assertEqual(rec2["medical_record_number"], "[REDACTED]")
            self.assertEqual(rec2["physician"], "[REDACTED]")

if __name__ == '__main__':
    unittest.main()
