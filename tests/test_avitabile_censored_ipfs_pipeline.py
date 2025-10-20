#!/usr/bin/env python3
"""Test for the Avitabile censored-IPFS pipeline demo."""
import sys, os, unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from demo.avitabile_censored_ipfs_pipeline import run_avitabile_censored_ipfs_pipeline_demo


class TestAvitabileCensoredPipelineDemo(unittest.TestCase):
    def test_run(self):
        from shutil import which
        if which("snarkjs") is None:
            self.skipTest("snarkjs CLI not available; real proof generation required")
        demo = run_avitabile_censored_ipfs_pipeline_demo()
        # Basic assertions: linkage exists for some patients
        self.assertGreater(len(demo.links), 0)
        # Ensure at least one mapping in contract state exists
        self.assertGreater(len(demo.engine.medical_contract.state.get("ipfs_mappings", {})), 0)


if __name__ == "__main__":
    unittest.main()
