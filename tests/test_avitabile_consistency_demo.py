#!/usr/bin/env python3
"""Unit test for the Avitabile consistency demo."""
import sys, os, unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from demos.avitabile_consistency_demo import run_avitabile_consistency_demo


class TestAvitabileConsistencyDemo(unittest.TestCase):
    def test_run(self):
        # Should run without raising and pass internal assertion
        run_avitabile_consistency_demo()


if __name__ == "__main__":
    unittest.main()

