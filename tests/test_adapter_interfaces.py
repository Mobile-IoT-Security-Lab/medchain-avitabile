#!/usr/bin/env python3
"""Comprehensive tests for all adapter interfaces.

Tests the adapters in simulation mode to ensure interfaces work correctly
without requiring external services.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestSnarkAdapterInterface(unittest.TestCase):
    """Test SNARK adapter interface and functionality."""
    
    def setUp(self):
        # Import inside test to handle optional dependencies
        try:
            from adapters.snark import SnarkClient
            self.snark_class = SnarkClient
        except ImportError:
            self.skipTest("SNARK adapter not available")
    
    def test_snark_client_initialization(self):
        """Test SnarkClient can be initialized."""
        client = self.snark_class()
        self.assertIsNotNone(client)
        self.assertIsInstance(client.circuits_dir, Path)
        self.assertIsInstance(client.build_dir, Path)
    
    def test_snark_client_configuration_flags(self):
        """Test configuration flag handling."""
        client = self.snark_class()
        
        # Test enabled check
        enabled = client.is_enabled()
        self.assertIsInstance(enabled, bool)
        
        # Test availability check
        available = client.is_available()
        self.assertIsInstance(available, bool)
    
    @patch.dict(os.environ, {"USE_REAL_SNARK": "0"})
    def test_snark_client_disabled_mode(self):
        """Test SNARK client behavior when disabled."""
        client = self.snark_class()
        
        # Should not be enabled
        self.assertFalse(client.is_enabled())
        
        # Methods should return None when disabled
        result = client.generate_witness({"test": 1}, {"private": 2})
        self.assertIsNone(result)
        
        result = client.prove_redaction({"test": 1}, {"private": 2})
        self.assertIsNone(result)
    
    @patch('subprocess.run')
    def test_snark_witness_generation_interface(self, mock_run):
        """Test witness generation interface."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with patch.dict(os.environ, {"USE_REAL_SNARK": "1"}):
            client = self.snark_class()
            
            # Mock file existence checks
            with patch.object(client.wasm_path, 'exists', return_value=True), \
                 patch.object(client.zkey_path, 'exists', return_value=True), \
                 patch.object(client.vkey_path, 'exists', return_value=True):
                
                # Mock witness file creation
                with patch('pathlib.Path.exists', return_value=True):
                    result = client.generate_witness({"public": 1}, {"private": 2})
                    
                    # Should call snarkjs
                    self.assertTrue(mock_run.called)
                    args = mock_run.call_args[0][0]
                    self.assertEqual(args[0], "snarkjs")
                    self.assertEqual(args[1], "wtns")
                    self.assertEqual(args[2], "calculate")
    
    def test_snark_calldata_formatting(self):
        """Test calldata formatting for Solidity."""
        client = self.snark_class()
        
        # Mock proof structure
        mock_proof = {
            "pi_a": ["123", "456", "1"],
            "pi_b": [["789", "012"], ["345", "678"]],
            "pi_c": ["901", "234"]
        }
        mock_public = ["111", "222"]
        
        result = client.format_calldata(mock_proof, mock_public)
        
        self.assertIsNotNone(result)
        pA, pB, pC, pubSignals = result
        
        # Check structure
        self.assertEqual(len(pA), 2)
        self.assertEqual(len(pB), 2)
        self.assertEqual(len(pB[0]), 2)
        self.assertEqual(len(pC), 2)
        self.assertEqual(len(pubSignals), 2)
        
        # Check types
        self.assertIsInstance(pA[0], int)
        self.assertIsInstance(pubSignals[0], int)


class TestEVMAdapterInterface(unittest.TestCase):
    """Test EVM adapter interface."""
    
    def setUp(self):
        try:
            from adapters.evm import EVMClient
            self.evm_class = EVMClient
        except ImportError:
            self.skipTest("EVM adapter not available")
    
    def test_evm_client_initialization(self):
        """Test EVMClient can be initialized."""
        with patch('web3.Web3'):
            client = self.evm_class()
            self.assertIsNotNone(client)
    
    @patch.dict(os.environ, {"USE_REAL_EVM": "0"})
    def test_evm_client_disabled_mode(self):
        """Test EVM client behavior when disabled."""
        with patch('web3.Web3'):
            client = self.evm_class()
            
            # Should handle disabled mode gracefully
            result = client.is_connected()
            self.assertIsInstance(result, bool)
    
    def test_evm_interface_methods(self):
        """Test EVM client has required interface methods."""
        with patch('web3.Web3'), \
             patch.object(self.evm_class, 'is_connected', return_value=True):
            
            client = self.evm_class()
            
            # Check required methods exist
            self.assertTrue(hasattr(client, 'deploy'))
            self.assertTrue(hasattr(client, 'storeMedicalData'))
            self.assertTrue(hasattr(client, 'requestDataRedaction'))
            self.assertTrue(hasattr(client, 'get_events'))
            self.assertTrue(callable(client.deploy))


class TestIPFSAdapterInterface(unittest.TestCase):
    """Test IPFS adapter interface."""
    
    def setUp(self):
        try:
            from adapters.ipfs import get_ipfs_client
            self.get_client = get_ipfs_client
        except ImportError:
            self.skipTest("IPFS adapter not available")
    
    def test_ipfs_client_factory(self):
        """Test IPFS client factory function."""
        # Should return a client (real or fake)
        client = self.get_client()
        self.assertIsNotNone(client)
    
    @patch.dict(os.environ, {"USE_REAL_IPFS": "0"})
    def test_ipfs_simulation_mode(self):
        """Test IPFS client in simulation mode."""
        client = self.get_client()
        
        # Should have required interface methods
        self.assertTrue(hasattr(client, 'add'))
        self.assertTrue(hasattr(client, 'get'))
        self.assertTrue(hasattr(client, 'pin'))
        self.assertTrue(hasattr(client, 'unpin'))
        self.assertTrue(hasattr(client, 'stat'))
        
        # Test basic functionality
        content = "test content"
        cid = client.add(content)
        self.assertIsInstance(cid, str)
        self.assertTrue(len(cid) > 0)
        
        # Test roundtrip
        retrieved = client.get(cid)
        self.assertEqual(retrieved, content)
    
    def test_ipfs_interface_methods(self):
        """Test IPFS client interface completeness."""
        client = self.get_client()
        
        # All required methods should be callable
        required_methods = ['add', 'get', 'pin', 'unpin', 'rm', 'stat']
        for method in required_methods:
            self.assertTrue(hasattr(client, method), f"Missing method: {method}")
            self.assertTrue(callable(getattr(client, method)), f"Method not callable: {method}")


class TestAdapterIntegration(unittest.TestCase):
    """Test adapter integration with medical redaction engine."""
    
    def test_hybrid_snark_manager_integration(self):
        """Test HybridSNARKManager uses adapters correctly."""
        try:
            from medical.MedicalRedactionEngine import HybridSNARKManager
        except ImportError:
            self.skipTest("Medical redaction engine not available")
        
        # Test with no client (simulation mode)
        manager = HybridSNARKManager(None)
        self.assertFalse(manager.use_real)
        
        # Test proof creation fallback
        proof = manager.create_redaction_proof({"redaction_type": "DELETE"})
        self.assertIsNotNone(proof)
    
    def test_medical_redaction_engine_adapter_integration(self):
        """Test medical redaction engine integrates adapters properly."""
        try:
            from medical.MedicalRedactionEngine import MyRedactionEngine
        except ImportError:
            self.skipTest("Medical redaction engine not available")
        
        with patch.dict(os.environ, {"USE_REAL_SNARK": "0", "USE_REAL_EVM": "0"}):
            engine = MyRedactionEngine()
            
            # Should have adapter components
            self.assertIsNotNone(engine.snark_manager)
            self.assertIsNotNone(engine.medical_contract)
            
            # Test redaction request creation
            request = engine.create_redaction_request(
                target_contract="TestContract",
                target_function="testFunction",
                target_data_field="testField",
                redaction_type="DELETE",
                requester="test_user",
                reason="Test redaction"
            )
            self.assertIsNotNone(request)


if __name__ == "__main__":
    unittest.main()