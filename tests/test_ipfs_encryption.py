#!/usr/bin/env python3
"""AES-GCM encryption roundtrip tests for IPFS dataset manager.

Skips when cryptography AESGCM is not available.
"""
import os
import sys
import unittest
import base64


# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
except Exception:  # pragma: no cover
    AESGCM = None  # type: ignore

from medical.MedicalDataIPFS import (
    IPFSMedicalDataManager,
    FakeIPFSClient,
    MedicalDatasetGenerator,
)


@unittest.skipIf(AESGCM is None, "cryptography AESGCM not available")
class TestIPFSAESGCM(unittest.TestCase):
    def setUp(self):
        # Generate a random AES-256 key and export as base64
        key = os.urandom(32)
        self._prev_key = os.environ.get("IPFS_ENC_KEY")
        os.environ["IPFS_ENC_KEY"] = base64.b64encode(key).decode()

        self.ipfs = FakeIPFSClient()
        self.mgr = IPFSMedicalDataManager(self.ipfs)
        self.gen = MedicalDatasetGenerator()

    def tearDown(self):
        # Restore env var
        if self._prev_key is None:
            os.environ.pop("IPFS_ENC_KEY", None)
        else:
            os.environ["IPFS_ENC_KEY"] = self._prev_key

    def test_encrypt_then_download_roundtrip(self):
        ds = self.gen.generate_dataset(num_patients=5, dataset_name="AES Test")
        h = self.mgr.upload_dataset(ds, encrypt=True)
        self.assertTrue(isinstance(h, str) and len(h) > 0)

        # Stored payload should be an AES-GCM envelope and should not contain plaintext markers
        stored = self.ipfs.get(h)
        self.assertIsInstance(stored, str)
        self.assertIn('"enc": "AES-GCM"', stored)
        self.assertIn('"ciphertext"', stored)
        self.assertIn('"nonce"', stored)
        self.assertIn('"kid"', stored)
        self.assertNotIn('"patient_records"', stored)  # plaintext not present in envelope

        # Download + decrypt
        ds2 = self.mgr.download_dataset(h)
        self.assertIsNotNone(ds2)
        self.assertEqual(len(ds2.patient_records), len(ds.patient_records))
        self.assertEqual(ds2.name, ds.name)

    def test_decrypt_fails_without_key(self):
        # Upload with key present
        ds = self.gen.generate_dataset(num_patients=3, dataset_name="AES NoKey Test")
        h = self.mgr.upload_dataset(ds, encrypt=True)
        stored = self.ipfs.get(h)
        self.assertIn('"enc": "AES-GCM"', stored)

        # Remove key and create a fresh manager (so it does not cache the key)
        os.environ.pop("IPFS_ENC_KEY", None)
        mgr2 = IPFSMedicalDataManager(self.ipfs)
        # Attempt to download should fail gracefully (returns None)
        ds_fail = mgr2.download_dataset(h)
        self.assertIsNone(ds_fail)


if __name__ == "__main__":
    unittest.main()
