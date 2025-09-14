#!/usr/bin/env python3
"""Integration test for EVM path (skipped unless USE_REAL_EVM=1).

Requires:
- USE_REAL_EVM=1
- Hardhat artifacts in contracts/artifacts
- Local devnet RPC (e.g., Hardhat/Anvil) in WEB3_PROVIDER_URI
"""
import os
import unittest


@unittest.skipUnless(os.getenv("USE_REAL_EVM") == "1", "Requires USE_REAL_EVM=1")
class TestEvmIntegration(unittest.TestCase):
    def setUp(self):
        from adapters.evm import get_evm_client
        self.client = get_evm_client()
        if self.client is None:
            self.skipTest("EVM client unavailable or RPC not reachable")

    def test_deploy_and_events(self):
        # Deploy manager (skip if artifacts missing)
        deployed = self.client.deploy("MedicalDataManager")
        if not deployed:
            self.skipTest("Artifacts not found; compile contracts first")
        addr, manager = deployed
        # Call store
        # Provide a dummy ciphertext hash (32 bytes)
        txh = self.client.storeMedicalData(manager, "PAT_INT_001", "QmCID123", b"\x00" * 32)
        self.assertTrue(txh)
        # Call redaction
        txh2 = self.client.requestDataRedaction(manager, "PAT_INT_001", "DELETE", "test")
        self.assertTrue(txh2)
        # Read events
        ds = self.client.get_events(manager, "DataStored")
        rr = self.client.get_events(manager, "RedactionRequested")
        self.assertTrue(len(ds) >= 1)
        self.assertTrue(len(rr) >= 1)


if __name__ == "__main__":
    unittest.main()
