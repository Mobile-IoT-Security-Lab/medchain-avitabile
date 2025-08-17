#!/usr/bin/env python3
"""
Unit test for the Enhanced Medical Redaction Engine demonstration in MedicalRedactionEngine.py
"""
import sys
import os
import unittest

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Enhanced.MedicalRedactionEngine import test_enhanced_medical_redaction


class TestMedicalRedactionEngine(unittest.TestCase):
    """Test the enhanced medical data redaction system demonstration."""

    def test_enhanced_medical_redaction(self):
        # The demo function should run without raising exceptions
        test_enhanced_medical_redaction()


if __name__ == '__main__':
    unittest.main()
