#!/usr/bin/env python3
"""Standalone runner for the medical redaction demo."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from medical.MedicalRedactionEngine import test_my_medical_redaction


if __name__ == "__main__":
    test_my_medical_redaction()
