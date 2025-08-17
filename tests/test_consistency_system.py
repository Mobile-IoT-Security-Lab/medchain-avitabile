#!/usr/bin/env python3
"""
Unit test for the Proof-of-Consistency demonstration in ProofOfConsistency.py
"""
import sys
import os
import unittest

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ZK.ProofOfConsistency import test_consistency_system


class TestConsistencySystem(unittest.TestCase):
    """Test the proof-of-consistency system demonstration."""

    def test_consistency_system(self):
        # The demo function should run without raising exceptions
        test_consistency_system()


if __name__ == '__main__':
    unittest.main()
