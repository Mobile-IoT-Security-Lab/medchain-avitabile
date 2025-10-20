#!/usr/bin/env python3
"""Specific tests for SNARK adapter functionality.

Tests the SnarkClient implementation in detail, including edge cases
and error handling.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open


class TestSnarkClientDetailed(unittest.TestCase):
    """Detailed tests for SnarkClient implementation."""
    
    def setUp(self):
        try:
            from adapters.snark import SnarkClient
            self.SnarkClient = SnarkClient
        except ImportError:
            self.skipTest("SNARK adapter not available")
    
    def test_path_configuration(self):
        """Test circuit path configuration."""
        client = self.SnarkClient()
        
        # Check paths are properly configured
        self.assertTrue(str(client.circuits_dir).endswith('circuits'))
        self.assertTrue(str(client.build_dir).endswith('build'))
        self.assertTrue(str(client.wasm_path).endswith('.wasm'))
        self.assertTrue(str(client.zkey_path).endswith('.zkey'))
        self.assertTrue(str(client.vkey_path).endswith('.json'))
    
    def test_custom_circuits_directory(self):
        """Test custom circuits directory configuration."""
        with tempfile.TemporaryDirectory() as tmp:
            custom_dir = Path(tmp)
            custom_build = custom_dir / "build"
            (custom_build / "redaction_js").mkdir(parents=True, exist_ok=True)
            (custom_build / "redaction_js" / "redaction.wasm").touch()
            (custom_build / "redaction_final.zkey").touch()
            (custom_build / "verification_key.json").touch()
            with patch.dict(os.environ, {"CIRCUITS_DIR": str(custom_dir)}):
                client = self.SnarkClient()
                self.assertEqual(client.circuits_dir, custom_dir)
    
    def test_availability_checks(self):
        """Test circuit artifact availability checks."""
        client = self.SnarkClient()
        
        # Test when files don't exist using patch
        with patch('pathlib.Path.exists', return_value=False):
            self.assertFalse(client.is_available())
        
        # Test when all files exist
        with patch('pathlib.Path.exists', return_value=True):
            self.assertTrue(client.is_available())
    
    @patch('subprocess.run')
    def test_snarkjs_command_execution(self, mock_run):
        """Test snarkjs command execution wrapper."""
        mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
        
        client = self.SnarkClient()
        result = client._run_snarkjs(["--version"])
        
        # Should call subprocess with correct command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "snarkjs")
        self.assertEqual(args[1], "--version")
    
    @patch('subprocess.run')
    def test_snarkjs_command_failure(self, mock_run):
        """Test snarkjs command failure handling."""
        from subprocess import CalledProcessError
        
        mock_run.side_effect = CalledProcessError(1, ["snarkjs"], stderr="Command failed")
        
        client = self.SnarkClient()
        
        with self.assertRaises(RuntimeError) as ctx:
            client._run_snarkjs(["--invalid"])
        
        self.assertIn("snarkjs command failed", str(ctx.exception))
    
    @patch('subprocess.run')
    def test_snarkjs_not_found(self, mock_run):
        """Test snarkjs not found error handling."""
        mock_run.side_effect = FileNotFoundError("snarkjs not found")
        
        client = self.SnarkClient()
        
        with self.assertRaises(RuntimeError) as ctx:
            client._run_snarkjs(["--version"])
        
        self.assertIn("snarkjs not found", str(ctx.exception))
        self.assertIn("npm install -g snarkjs", str(ctx.exception))
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('subprocess.run')
    def test_witness_generation_success(self, mock_run, mock_temp):
        """Test successful witness generation."""
        # Mock temporary file
        mock_temp.return_value.__enter__.return_value.name = "/tmp/input.json"
        mock_temp.return_value.__enter__.return_value.write = Mock()
        
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock file operations
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'unlink'):
            
            client = self.SnarkClient()
            result = client.generate_witness({"pub": 1}, {"priv": 2})
            
            # Should return witness path
            self.assertIsNotNone(result)
            self.assertIsInstance(result, Path)
    
    def test_witness_generation_missing_artifacts(self):
        """Witness generation should raise when artifacts are unavailable."""
        client = self.SnarkClient()
        client.is_available = lambda: False
        with self.assertRaises(RuntimeError):
            client.generate_witness({"pub": 1}, {"priv": 2})
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('subprocess.run')
    def test_proof_generation_success(self, mock_run, mock_file):
        """Test successful proof generation."""
        # Mock proof and public files
        mock_proof = {"pi_a": ["1", "2", "1"], "pi_b": [["3", "4"], ["5", "6"]], "pi_c": ["7", "8"]}
        mock_public = ["9", "10"]
        
        mock_file.return_value.read.side_effect = [
            json.dumps(mock_proof),
            json.dumps(mock_public)
        ]
        
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            client = self.SnarkClient()
            witness_path = Path("/tmp/witness.wtns")
            
            result = client.prove(witness_path)
            
            self.assertIsNotNone(result)
            proof, public_signals = result
            self.assertEqual(proof, mock_proof)
            self.assertEqual(public_signals, mock_public)
    
    @patch('tempfile.NamedTemporaryFile')
    def test_proof_verification_interface(self, mock_temp):
        """Test proof verification interface."""
        client = self.SnarkClient()
        
        mock_temp.return_value.__enter__.return_value.name = "/tmp/temp.json"
        mock_temp.return_value.__exit__.return_value = False
        
        mock_proof = {"pi_a": ["1", "2"], "pi_b": [["3", "4"], ["5", "6"]], "pi_c": ["7", "8"]}
        mock_public = ["9", "10"]
        
        client.is_available = lambda: True
        with patch.object(client, '_run_snarkjs', return_value=MagicMock(stdout="OK!")):
            result = client.verify_proof(mock_proof, mock_public)
            self.assertTrue(result)
    
    def test_calldata_formatting_edge_cases(self):
        """Test calldata formatting with edge cases."""
        client = self.SnarkClient()
        
        # Test with None inputs
        result = client.format_calldata(None, None)
        self.assertIsNone(result)
        
        # Test with empty proof
        result = client.format_calldata({}, [])
        self.assertIsNone(result)
        
        # Test with malformed proof
        malformed_proof = {"pi_a": "invalid", "pi_b": [], "pi_c": []}
        result = client.format_calldata(malformed_proof, ["1"])
        self.assertIsNone(result)
        
        # Test with non-numeric values
        invalid_proof = {"pi_a": ["abc", "def"], "pi_b": [["1", "2"], ["3", "4"]], "pi_c": ["5", "6"]}
        result = client.format_calldata(invalid_proof, ["1"])
        self.assertIsNone(result)
    
    def test_prove_redaction_integration(self):
        """Test complete redaction proof generation."""
        client = self.SnarkClient()
        
        # Test with mocked successful generation
        with patch.object(client, 'generate_witness', return_value=Path("/tmp/witness.wtns")), \
             patch.object(client, 'prove', return_value=({}, [])), \
             patch.object(client, 'verify_proof', return_value=True), \
             patch.object(client, 'format_calldata', return_value=([], [], [], [])):
            
            result = client.prove_redaction({"pub": 1}, {"priv": 2})
            
            self.assertIsNotNone(result)
            self.assertIn("proof", result)
            self.assertIn("public_signals", result)
            self.assertIn("calldata", result)
            self.assertIn("verified", result)
            self.assertTrue(result["verified"])
        
        # Test failure path due to missing artifacts
        def raise_missing(*_args, **_kwargs):
            raise RuntimeError("missing artifacts")
        client.generate_witness = raise_missing
        with self.assertRaises(RuntimeError):
            client.prove_redaction({"pub": 1}, {"priv": 2})


class TestSnarkAdapterMocking(unittest.TestCase):
    """Test SNARK adapter mocking and failure modes."""
    
    def test_import_failure_handling(self):
        """HybridSNARKManager should raise when no real client is provided."""
        try:
            from medical.MedicalRedactionEngine import HybridSNARKManager
        except ImportError:
            self.skipTest("Medical redaction engine not available")
        
        with self.assertRaises(ValueError):
            HybridSNARKManager(None)
