#!/usr/bin/env python3
"""
Unit test for the IPFS medical data management system demonstration in MedicalDataIPFS.py
"""
import sys
import os
import unittest

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medical.MedicalDataIPFS import test_ipfs_medical_data_system


class TestIPFSMedicalDataSystem(unittest.TestCase):
    """Test the IPFS medical data management system demonstration."""

    def test_ipfs_medical_data_system(self):
        # The demo function should run without raising exceptions
        test_ipfs_medical_data_system()


if __name__ == '__main__':
    unittest.main()
