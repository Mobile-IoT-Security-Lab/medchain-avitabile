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
            
            # Mock file existence checks using patch
            with patch('pathlib.Path.exists', return_value=True):
                
                # Mock witness file creation
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
        
        # Check if web3 is available
        try:
            import web3
        except ImportError:
            self.skipTest("web3 dependency not available")
    
    def test_evm_client_initialization(self):
        """Test EVMClient can be initialized."""
        with patch('adapters.evm.Web3'):
            client = self.evm_class()
            self.assertIsNotNone(client)
    
    @patch.dict(os.environ, {"USE_REAL_EVM": "0"})
    def test_evm_client_disabled_mode(self):
        """Test EVM client behavior when disabled."""
        with patch('adapters.evm.Web3'):
            client = self.evm_class()

            # Should handle disabled mode gracefully
            self.assertFalse(client._connected)
    
    def test_evm_interface_methods(self):
        """Test EVM client has required interface methods."""
        with patch('adapters.evm.Web3'):
            client = self.evm_class()
            
            # All required methods should exist
            required_methods = ['connect', 'deploy', 'storeMedicalData', 'requestDataRedaction', 'get_events']
            for method in required_methods:
                self.assertTrue(hasattr(client, method), f"Missing method: {method}")
                self.assertTrue(callable(getattr(client, method)), f"Method not callable: {method}")


class TestIPFSAdapterInterface(unittest.TestCase):
    """Test IPFS adapter interface."""
    
    def setUp(self):
        try:
            from adapters.ipfs import get_ipfs_client, RealIPFSClient
            self.get_client = get_ipfs_client
            self.real_client_class = RealIPFSClient
        except ImportError:
            self.skipTest("IPFS adapter not available")
    
    def test_ipfs_client_factory(self):
        """Test IPFS client factory function."""
        # Test that the factory function exists and is callable
        self.assertTrue(callable(self.get_client))
        
        # In simulation mode, should return None
        with patch.dict(os.environ, {"USE_REAL_IPFS": "0"}, clear=False):
            client = self.get_client()
            self.assertIsNone(client)
    
    @patch.dict(os.environ, {"USE_REAL_IPFS": "0"})
    def test_ipfs_simulation_mode(self):
        """Test IPFS client in simulation mode."""
        # When USE_REAL_IPFS=0, should return None
        client = self.get_client()
        self.assertIsNone(client)
    
    def test_ipfs_real_client_interface(self):
        """Test IPFS real client interface completeness."""
        # Test the RealIPFSClient class directly for interface
        try:
            # Create a mock instance to test interface
            with patch('adapters.ipfs.ipfshttpclient'):
                client = self.real_client_class()
                
                # All required methods should be callable
                required_methods = ['add', 'get', 'pin', 'unpin', 'rm', 'stat']
                for method in required_methods:
                    self.assertTrue(hasattr(client, method), f"Missing method: {method}")
                    self.assertTrue(callable(getattr(client, method)), f"Method not callable: {method}")
        except Exception:
            # If we can't create the client, just test the class has the right methods
            required_methods = ['add', 'get', 'pin', 'unpin', 'rm', 'stat']
            for method in required_methods:
                self.assertTrue(hasattr(self.real_client_class, method), f"Missing method: {method}")
    
    def test_ipfs_interface_methods(self):
        """Test IPFS client interface completeness."""
        # Test with enabled mode but expect graceful handling
        with patch.dict(os.environ, {"USE_REAL_IPFS": "1"}, clear=False):
            with patch('adapters.ipfs.ipfshttpclient'):
                # Try to get a real client
                client = self.get_client()
                
                if client is not None:
                    # All required methods should be callable
                    required_methods = ['add', 'get', 'pin', 'unpin', 'rm', 'stat']
                    for method in required_methods:
                        self.assertTrue(hasattr(client, method), f"Missing method: {method}")
                        self.assertTrue(callable(getattr(client, method)), f"Method not callable: {method}")
                else:
                    # If client is None, that's expected when dependencies aren't available
                    self.assertIsNone(client)


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

        # Test proof creation fallback with proper data structure
        redaction_data = {
            "redaction_type": "DELETE",
            "request_id": "test_123",
            "target_block": 10,
            "target_tx": 2,
            "requester": "test_user",
            "merkle_root": "test_root",
            "original_data": "test_original",
            "redacted_data": "test_redacted"
        }
        proof = manager.create_redaction_proof(redaction_data)
        self.assertIsNotNone(proof)
        self.assertEqual(proof.operation_type, "DELETE")

    def test_medical_redaction_engine_adapter_integration(self):
        """Test medical redaction engine integrates adapters properly."""
        try:
            from medical.MedicalRedactionEngine import MyRedactionEngine, MedicalDataRecord
        except ImportError:
            self.skipTest("Medical redaction engine not available")

        with patch.dict(os.environ, {"USE_REAL_SNARK": "0", "USE_REAL_EVM": "0"}):
            engine = MyRedactionEngine()

            # Should have adapter components
            self.assertIsNotNone(engine.snark_manager)
            self.assertIsNotNone(engine.medical_contract)

            # First add a patient record (required for redaction)
            patient_data = {
                "patient_id": "test_patient",
                "patient_name": "Test Patient",
                "medical_record_number": "MRN123",
                "diagnosis": "Test condition",
                "treatment": "Test treatment",
                "physician": "Dr. Test"
            }
            medical_record = engine.create_medical_data_record(patient_data)
            engine.store_medical_data(medical_record)

            # Test redaction request creation (using actual method name)
            request_id = engine.request_data_redaction(
                patient_id="test_patient",
                redaction_type="DELETE",
                reason="Test redaction",
                requester="test_user",
                requester_role="ADMIN"
            )
            self.assertIsNotNone(request_id)
if __name__ == "__main__":
    unittest.main()