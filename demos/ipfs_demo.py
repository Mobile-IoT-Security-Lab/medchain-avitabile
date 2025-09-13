#!/usr/bin/env python3
"""Standalone runner for the IPFS medical data demo."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from medical.MedicalDataIPFS import test_ipfs_medical_data_system


if __name__ == "__main__":
    test_ipfs_medical_data_system()

