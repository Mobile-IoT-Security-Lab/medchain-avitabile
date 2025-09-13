#!/usr/bin/env python3
"""Unit test for the Avitabile redaction workflow demo."""
import sys, os, unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from demo.avitabile_redaction_demo import run_avitabile_redaction_demo


class TestAvitabileRedactionDemo(unittest.TestCase):
    def test_run(self):
        engine, rid_delete, rid_anon = run_avitabile_redaction_demo()
        self.assertTrue(rid_delete)
        self.assertTrue(rid_anon)
        # Validate audit history has 2 entries
        self.assertGreaterEqual(len(engine.get_redaction_history()), 2)


if __name__ == "__main__":
    unittest.main()
