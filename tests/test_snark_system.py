#!/usr/bin/env python3
"""
Unit test for the SNARK system demonstration in SNARKs.py

### Bookmark1 for next meeting
"""
import sys
import os
import unittest

# Allow imports from project root
d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(d)

from ZK.SNARKs import test_snark_system


class TestSNARKSystem(unittest.TestCase):
    """Test the SNARK system demonstration."""

    def test_snark_system(self):
        # The demo function should run without raising exceptions
        test_snark_system()


if __name__ == '__main__':
    unittest.main()
