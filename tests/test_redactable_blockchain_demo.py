#!/usr/bin/env python3
"""
Unit test for the Redactable Blockchain demo (Ateniese-style chameleon hash redaction).
"""
import sys
import os
import unittest

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demos.redactable_blockchain_demo import run_demo


class TestRedactableBlockchainDemo(unittest.TestCase):
    """Ensure the redactable blockchain demo runs without exceptions."""

    def test_run_demo(self):
        # The demo function performs internal assertions; running it is sufficient
        run_demo()


if __name__ == '__main__':
    unittest.main()

