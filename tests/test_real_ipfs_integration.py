#!/usr/bin/env python3
"""Integration test for real IPFS client.

Runs only when USE_REAL_IPFS=1 and a local IPFS daemon is reachable.
"""
import os
import unittest

@unittest.skipUnless(os.getenv("USE_REAL_IPFS") == "1", "Requires USE_REAL_IPFS=1")
class TestRealIPFSIntegration(unittest.TestCase):
    def setUp(self):
        # Import inside test to avoid mandatory dependency
        from adapters.ipfs import get_ipfs_client
        self.client = get_ipfs_client()
        self.assertIsNotNone(
            self.client,
            "Real IPFS client not available or daemon not reachable.\n"
            "Start a local node (ipfs daemon) or set IPFS_API_ADDR to your API endpoint\n"
            "(e.g., /ip4/127.0.0.1/tcp/5001/http or http://127.0.0.1:5001)."
        )

    def test_add_and_get_roundtrip(self):
        content = "hello-medchain-real-ipfs"
        cid = self.client.add(content, pin=True)
        self.assertTrue(isinstance(cid, str) and len(cid) > 0)
        fetched = self.client.get(cid)
        self.assertEqual(fetched, content)
        st = self.client.stat(cid)
        self.assertIsNotNone(st)
        self.assertIn("size", st)


if __name__ == "__main__":
    unittest.main()

