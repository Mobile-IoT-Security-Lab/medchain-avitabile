#!/usr/bin/env python3
"""Tests for KeyProvider implementations (Env and File).
"""
import os
import sys
import unittest
import tempfile
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
except Exception:  # pragma: no cover
    AESGCM = None  # type: ignore

from medical.key_provider import EnvKeyProvider, FileKeyProvider
from medical.MedicalDataIPFS import IPFSMedicalDataManager, FakeIPFSClient
from medical.MedicalDataIPFS import MedicalDatasetGenerator


class TestEnvKeyProvider(unittest.TestCase):
    def setUp(self):
        self.prev_key = os.environ.get("IPFS_ENC_KEY")
        self.prev_id = os.environ.get("IPFS_ENC_KEY_ID")

    def tearDown(self):
        if self.prev_key is None:
            os.environ.pop("IPFS_ENC_KEY", None)
        else:
            os.environ["IPFS_ENC_KEY"] = self.prev_key
        if self.prev_id is None:
            os.environ.pop("IPFS_ENC_KEY_ID", None)
        else:
            os.environ["IPFS_ENC_KEY_ID"] = self.prev_id

    def test_env_provider_roundtrip(self):
        key = os.urandom(32)
        os.environ["IPFS_ENC_KEY"] = base64.b64encode(key).decode()
        prov = EnvKeyProvider()
        k, kid = prov.get_active_key()
        self.assertEqual(k, key)
        self.assertTrue(kid)


@unittest.skipIf(AESGCM is None, "cryptography AESGCM not available")
class TestFileKeyProvider(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "keystore.json")
        self.passphrase = "test-passphrase"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_file_provider_create_and_use(self):
        prov = FileKeyProvider(self.path, passphrase=self.passphrase)
        k, kid = prov.rotate()  # create
        self.assertIsNotNone(k)
        self.assertTrue(os.path.exists(self.path))
        k2, kid2 = prov.get_active_key()
        self.assertEqual(k, k2)
        self.assertEqual(kid, kid2)

        # Use with manager to encrypt/decrypt
        ipfs = FakeIPFSClient()
        mgr = IPFSMedicalDataManager(ipfs, key_provider=prov)
        ds = MedicalDatasetGenerator().generate_dataset(num_patients=2, dataset_name="ProvTest")
        h = mgr.upload_dataset(ds, encrypt=True)
        stored = ipfs.get(h)
        self.assertIn('"AES-GCM"', stored)
        self.assertIn('"kid"', stored)
        ds2 = mgr.download_dataset(h)
        self.assertIsNotNone(ds2)

    def test_file_provider_multi_key_decrypt_old(self):
        prov = FileKeyProvider(self.path, passphrase=self.passphrase)
        # First key
        k1, kid1 = prov.rotate()
        ipfs = FakeIPFSClient()
        mgr1 = IPFSMedicalDataManager(ipfs, key_provider=prov)
        ds1 = MedicalDatasetGenerator().generate_dataset(num_patients=2, dataset_name="OldKey")
        h_old = mgr1.upload_dataset(ds1, encrypt=True)

        # Rotate to a new key
        k2, kid2 = prov.rotate()
        self.assertNotEqual(kid1, kid2)
        # New manager uses provider with new active key; should still decrypt old envelope via kid lookup
        mgr2 = IPFSMedicalDataManager(ipfs, key_provider=prov)
        ds1_again = mgr2.download_dataset(h_old)
        self.assertIsNotNone(ds1_again)
