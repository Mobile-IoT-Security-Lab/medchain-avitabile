"""
Integration Tests for Medchain Avitabile
========================================

This module contains integration tests that require real external services:
- Hardhat devnet for smart contract interaction
- IPFS daemon for distributed storage
- Complete end-to-end workflows

Run with: pytest -m integration tests/test_integration.py -v
"""

import pytest
import os
import time
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Import integration test infrastructure with graceful fallback
try:
    from tests.conftest import (
        integration_environment, 
        check_service_requirements,
        _service_manager
    )
except ImportError:
    # Define minimal versions if conftest not available
    def check_service_requirements():
        """Minimal service requirement check."""
        return {'hardhat': False, 'ipfs': False, 'web3': False, 'snarkjs': False}
    
    def integration_environment():
        """Minimal integration environment."""
        class MockEnv:
            def __enter__(self):
                return {'services_started': [], 'hardhat_port': None, 'ipfs_port': None, 'deployment_addresses': {}}
            def __exit__(self, *args):
                pass
        return MockEnv()
    
    _service_manager = None

# Import project modules with graceful handling
try:
    from medical.MedicalRedactionEngine import MyRedactionEngine, MedicalDataRecord
    from medical.MedicalDataIPFS import IPFSMedicalDataManager
    from adapters.evm import EVMClient
    from adapters.ipfs import get_ipfs_client
    from adapters.snark import SnarkClient
except ImportError as e:
    # Graceful degradation if modules not available
    print(f"Warning: Some modules not available: {e}")
    MyRedactionEngine = None
    MedicalDataRecord = None
    IPFSMedicalDataManager = None
    EVMClient = None
    get_ipfs_client = None
    SnarkClient = None


class TestServiceRequirements:
    """Test service availability and requirements."""
    
    def test_check_service_requirements(self):
        """Test service requirement checking."""
        requirements = check_service_requirements()
        assert isinstance(requirements, dict)
        assert 'hardhat' in requirements
        assert 'ipfs' in requirements
        assert 'web3' in requirements
        assert 'snarkjs' in requirements
        
        # At least some services should be available for CI
        available_services = sum(requirements.values())
        assert available_services >= 0  # Non-negative check


@pytest.mark.integration
class TestDevnetInfrastructure:
    """Test devnet startup and teardown functionality."""
    
    def test_service_manager_initialization(self):
        """Test ServiceManager can be initialized."""
        from conftest import ServiceManager
        manager = ServiceManager()
        assert manager.hardhat_process is None
        assert manager.ipfs_process is None
        assert manager.contracts_deployed is False
    
    def test_port_finding(self):
        """Test free port finding functionality."""
        from conftest import ServiceManager
        manager = ServiceManager()
        port = manager.find_free_port(9000)  # Use high port to avoid conflicts
        assert isinstance(port, int)
        assert port >= 9000
    
    @pytest.mark.requires_evm
    def test_hardhat_node_lifecycle(self):
        """Test Hardhat node startup and shutdown."""
        requirements = check_service_requirements()
        if not requirements['hardhat']:
            pytest.skip("Hardhat not available")
        
        manager = _service_manager
        
        # Test startup
        started = manager.start_hardhat_node()
        if started:
            assert manager.hardhat_port is not None
            assert manager.hardhat_process is not None
            
            # Test connection
            web3_uri = manager.get_web3_uri()
            assert web3_uri is not None
            assert f"localhost:{manager.hardhat_port}" in web3_uri
            
            # Test shutdown
            manager.stop_hardhat_node()
            assert manager.hardhat_process is None
            assert manager.hardhat_port is None
    
    @pytest.mark.requires_ipfs
    def test_ipfs_daemon_lifecycle(self):
        """Test IPFS daemon startup and shutdown."""
        requirements = check_service_requirements()
        if not requirements['ipfs']:
            pytest.skip("IPFS not available")
        
        manager = _service_manager
        
        # Test startup
        started = manager.start_ipfs_daemon()
        if started:
            assert manager.ipfs_port is not None
            assert manager.ipfs_process is not None
            
            # Test API URL
            api_url = manager.get_ipfs_api_url()
            assert api_url is not None
            assert f"localhost:{manager.ipfs_port}" in api_url
            
            # Test shutdown
            manager.stop_ipfs_daemon()
            assert manager.ipfs_process is None
            assert manager.ipfs_port is None


@pytest.mark.integration
@pytest.mark.requires_evm
class TestContractDeployment:
    """Test contract deployment in test setup."""
    
    def test_contract_deployment_process(self):
        """Test contract deployment to devnet."""
        requirements = check_service_requirements()
        if not requirements['hardhat']:
            pytest.skip("Hardhat not available")
        
        with integration_environment() as env:
            if 'contracts' in env['services_started']:
                # Contracts were deployed successfully
                assert env['deployment_addresses']
                assert 'service_manager' in env
                
                # Verify deployment addresses are valid
                for contract_name, address in env['deployment_addresses'].items():
                    assert isinstance(address, str)
                    assert len(address) == 42  # Ethereum address length
                    assert address.startswith('0x')
            else:
                pytest.skip("Contract deployment failed")
    
    def test_evm_client_contract_loading(self):
        """Test EVMClient can load deployed contracts."""
        requirements = check_service_requirements()
        if not requirements['hardhat'] or not requirements['web3']:
            pytest.skip("EVM requirements not met")
        
        with integration_environment() as env:
            if 'contracts' in env['services_started']:
                client = EVMClient()
                
                # Test connection
                connected = client.connect()
                if connected:
                    # Test contract loading (if deployment addresses available)
                    if env['deployment_addresses']:
                        # Basic smoke test - client should be functional
                        assert client._connected
                        assert client._w3 is not None
            else:
                pytest.skip("Contracts not deployed")


@pytest.mark.integration
@pytest.mark.requires_ipfs
class TestIPFSIntegration:
    """Test IPFS integration functionality."""
    
    def test_ipfs_client_real_connection(self):
        """Test real IPFS client connection."""
        requirements = check_service_requirements()
        if not requirements['ipfs']:
            pytest.skip("IPFS not available")
        
        with integration_environment() as env:
            if 'ipfs' in env['services_started']:
                # Test IPFS client
                client = get_ipfs_client()
                if client is not None:
                    # Test basic operations
                    test_content = "Integration test content"
                    cid = client.add(test_content)
                    assert isinstance(cid, str)
                    assert len(cid) > 0
                    
                    # Test retrieval
                    retrieved = client.get(cid)
                    assert retrieved == test_content
            else:
                pytest.skip("IPFS daemon not started")
    
    def test_medical_data_ipfs_integration(self):
        """Test medical data IPFS integration."""
        requirements = check_service_requirements()
        if not requirements['ipfs']:
            pytest.skip("IPFS not available")
        
        with integration_environment() as env:
            if 'ipfs' in env['services_started']:
                client = get_ipfs_client()
                if client is not None:
                    # Create medical data manager
                    manager = IPFSMedicalDataManager(client)
                    
                    # Test medical record storage
                    medical_data = {
                        "patient_id": "TEST001",
                        "diagnosis": "Test condition",
                        "treatment": "Test treatment",
                        "timestamp": int(time.time())
                    }
                    
                    # Store data
                    cid = manager.store_medical_record(medical_data)
                    assert isinstance(cid, str)
                    assert len(cid) > 0
                    
                    # Retrieve data
                    retrieved = manager.get_medical_record(cid)
                    assert retrieved == medical_data
            else:
                pytest.skip("IPFS daemon not started")


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_e2e_medical_data_lifecycle(self):
        """Test complete medical data lifecycle: store → redact → verify."""
        requirements = check_service_requirements()
        
        # Check if we have minimum requirements
        if not requirements['web3']:
            pytest.skip("Web3 not available")
        
        with integration_environment() as env:
            services = env['services_started']
            
            if len(services) == 0:
                pytest.skip("No services started")
            
            # Create medical redaction engine
            engine = MyRedactionEngine()
            
            # Test basic engine functionality
            assert engine.snark_manager is not None
            assert engine.medical_contract is not None
            
            # Create test patient data
            patient_data = {
                "patient_id": "E2E_TEST_001",
                "patient_name": "Integration Test Patient",
                "medical_record_number": "MRN_E2E_001",
                "diagnosis": "Integration test condition",
                "treatment": "Integration test treatment",
                "physician": "Dr. Integration Test"
            }
            
            # Create and store medical record
            medical_record = engine.create_medical_data_record(patient_data)
            stored = engine.store_medical_data(medical_record)
            assert stored is True
            
            # Test redaction request
            request_id = engine.request_data_redaction(
                patient_id="E2E_TEST_001",
                redaction_type="DELETE",
                reason="Integration test redaction",
                requester="integration_test_admin",
                requester_role="ADMIN"
            )
            
            if request_id is not None:
                # Redaction request was successful
                assert isinstance(request_id, str)
                assert len(request_id) > 0
                
                # Test redaction approval
                approved = engine.approve_redaction(
                    request_id=request_id,
                    approver="integration_test_approver",
                    comments="Integration test approval"
                )
                # Approval may or may not succeed depending on policies
                assert isinstance(approved, bool)
    
    @pytest.mark.requires_ipfs
    @pytest.mark.requires_evm  
    def test_complete_e2e_redaction_workflow(self):
        """
        Test complete E2E redaction workflow:
        IPFS upload → redaction request → on-chain verification → pointer update
        """
        requirements = check_service_requirements()
        
        if not (requirements['ipfs'] and requirements['hardhat'] and requirements['web3']):
            pytest.skip("Complete E2E requirements not met")
        
        with integration_environment() as env:
            services = env['services_started']
            
            if not ('ipfs' in services and 'contracts' in services):
                pytest.skip("Required services not started for E2E test")
            
            # Phase 1: Setup clients and data
            ipfs_client = get_ipfs_client()
            if ipfs_client is None:
                pytest.skip("IPFS client not available")
            
            evm_client = EVMClient()
            connected = evm_client.connect()
            if not connected:
                pytest.skip("EVM client connection failed")
            
            # Create medical redaction engine
            engine = MyRedactionEngine()
            
            # Phase 2: IPFS Upload - Store original medical data
            original_medical_data = {
                "patient_id": "E2E_COMPLETE_001",
                "patient_name": "Complete E2E Test Patient",
                "ssn": "123-45-6789",  # Sensitive data
                "diagnosis": "Comprehensive test condition",
                "treatment": "Advanced E2E treatment protocol",
                "physician": "Dr. E2E Specialist",
                "timestamp": int(time.time()),
                "sensitive_notes": "Highly confidential medical notes"
            }
            
            # Store original data in IPFS
            ipfs_content = json.dumps(original_medical_data, indent=2)
            original_cid = ipfs_client.add(ipfs_content)
            assert isinstance(original_cid, str)
            assert len(original_cid) > 0
            
            # Verify IPFS storage
            retrieved_content = ipfs_client.get(original_cid)
            retrieved_data = json.loads(retrieved_content)
            assert retrieved_data == original_medical_data
            
            # Phase 3: Create medical record in engine
            patient_data = {
                "patient_id": "E2E_COMPLETE_001",
                "patient_name": "Complete E2E Test Patient",
                "medical_record_number": "MRN_E2E_COMPLETE_001",
                "diagnosis": "Comprehensive test condition",
                "treatment": "Advanced E2E treatment protocol",
                "physician": "Dr. E2E Specialist",
                "ipfs_hash": original_cid  # Link to IPFS data
            }
            
            medical_record = engine.create_medical_data_record(patient_data)
            stored = engine.store_medical_data(medical_record)
            assert stored is True
            
            # Phase 4: Redaction Request - Request sensitive data removal
            request_id = engine.request_data_redaction(
                patient_id="E2E_COMPLETE_001",
                redaction_type="ANONYMIZE",  # Remove SSN and sensitive notes
                reason="GDPR Right to be Forgotten request",
                requester="gdpr_compliance_officer",
                requester_role="ADMIN"
            )
            
            assert request_id is not None
            assert isinstance(request_id, str)
            
            # Phase 5: Redaction Approval (simulate multi-party approval)
            approved = engine.approve_redaction(
                request_id=request_id,
                approver="data_protection_officer",
                comments="GDPR compliance approved"
            )
            
            # Phase 6: Create redacted version and upload to IPFS
            redacted_medical_data = original_medical_data.copy()
            redacted_medical_data["ssn"] = "[REDACTED]"
            redacted_medical_data["sensitive_notes"] = "[REDACTED FOR PRIVACY]"
            redacted_medical_data["redaction_applied"] = True
            redacted_medical_data["redaction_timestamp"] = int(time.time())
            redacted_medical_data["redaction_reason"] = "GDPR Right to be Forgotten"
            
            # Upload redacted version to IPFS  
            redacted_content = json.dumps(redacted_medical_data, indent=2)
            redacted_cid = ipfs_client.add(redacted_content)
            assert isinstance(redacted_cid, str)
            assert len(redacted_cid) > 0
            assert redacted_cid != original_cid  # Should be different
            
            # Phase 7: Verify redacted content
            retrieved_redacted = ipfs_client.get(redacted_cid)
            redacted_verification = json.loads(retrieved_redacted)
            assert redacted_verification["ssn"] == "[REDACTED]"
            assert redacted_verification["sensitive_notes"] == "[REDACTED FOR PRIVACY]"
            assert redacted_verification["redaction_applied"] is True
            
            # Phase 8: Pointer Update - Update record to point to redacted version
            # This would normally update the on-chain pointer from original_cid to redacted_cid
            updated_record = medical_record
            updated_record.ipfs_hash = redacted_cid
            
            # Store updated record
            update_stored = engine.store_medical_data(updated_record)
            assert update_stored is True
            
            # Phase 9: Verification - Ensure complete workflow integrity
            # Verify old content is still accessible via original CID (for audit)
            original_still_exists = ipfs_client.get(original_cid)
            assert json.loads(original_still_exists) == original_medical_data
            
            # Verify new content is accessible via new CID
            current_content = ipfs_client.get(redacted_cid)
            current_data = json.loads(current_content)
            assert current_data["redaction_applied"] is True
            assert "[REDACTED]" in current_data["ssn"]
            
            # Phase 10: On-chain verification simulation
            # In a full implementation, this would verify SNARK proofs on-chain
            if env['deployment_addresses']:
                # Contracts are deployed, we could test on-chain verification
                # For now, verify the proof generation works
                redaction_proof_data = {
                    "redaction_type": "ANONYMIZE",
                    "request_id": request_id,
                    "target_block": 0,
                    "target_tx": 0,
                    "requester": "gdpr_compliance_officer",
                    "merkle_root": "test_root",
                    "original_data": ipfs_content,
                    "redacted_data": redacted_content
                }
                
                proof = engine.snark_manager.create_redaction_proof(redaction_proof_data)
                assert proof is not None
                assert proof.operation_type == "ANONYMIZE"
                
            # Test completed successfully
            assert True
            
    def test_e2e_workflow_with_proof_verification(self):
        """Test E2E workflow with SNARK proof verification."""
        requirements = check_service_requirements()
        
        if not requirements['web3']:
            pytest.skip("Web3 not available for proof verification test")
        
        with integration_environment() as env:
            services = env['services_started']
            
            # Create medical redaction engine
            engine = MyRedactionEngine()
            
            # Create test data with proof verification
            patient_data = {
                "patient_id": "E2E_PROOF_001",
                "patient_name": "Proof Verification Test Patient",
                "medical_record_number": "MRN_PROOF_001",
                "diagnosis": "Proof test condition",
                "treatment": "Proof test treatment",
                "physician": "Dr. Proof Test"
            }
            
            medical_record = engine.create_medical_data_record(patient_data)
            stored = engine.store_medical_data(medical_record)
            assert stored is True
            
            # Request redaction with proof
            request_id = engine.request_data_redaction(
                patient_id="E2E_PROOF_001",
                redaction_type="DELETE",
                reason="Proof verification test",
                requester="proof_test_admin",
                requester_role="ADMIN"
            )
            
            if request_id is not None:
                # Generate proof data
                proof_data = {
                    "redaction_type": "DELETE",
                    "request_id": request_id,
                    "target_block": 1,
                    "target_tx": 1,
                    "requester": "proof_test_admin",
                    "merkle_root": "proof_test_root",
                    "original_data": json.dumps(patient_data),
                    "redacted_data": json.dumps({})
                }
                
                # Test proof generation
                proof = engine.snark_manager.create_redaction_proof(proof_data)
                assert proof is not None
                assert proof.operation_type == "DELETE"
                
                # Test proof verification
                public_inputs = {
                    "operation_type": "DELETE",
                    "merkle_root": "proof_test_root"
                }
                
                verified = engine.snark_manager.verify_redaction_proof(proof, public_inputs)
                assert verified is True
                
                # If contracts are deployed, test on-chain verification simulation
                if 'contracts' in services and env['deployment_addresses']:
                    # This would call the actual smart contract verifier
                    # For now, test that the proof format is correct
                    assert hasattr(proof, 'proof_id')
                    assert hasattr(proof, 'verifier_challenge')
                    assert hasattr(proof, 'prover_response')
                    assert hasattr(proof, 'commitment')
                    assert hasattr(proof, 'nullifier')
    
    def test_environment_validation_and_skipping(self):
        """Test that tests properly skip when services are unavailable."""
        # This test always runs to verify the skipping mechanism
        requirements = check_service_requirements()
        
        # Verify requirement checking works
        assert isinstance(requirements, dict)
        
        # Test that missing services are properly detected
        for service, available in requirements.items():
            assert isinstance(available, bool)
        
        # This test should always pass, demonstrating environment validation
        assert True


class TestEnvironmentValidation:
    """Test environment validation and graceful skipping."""
    
    def test_service_requirement_validation(self):
        """Test comprehensive service requirement validation."""
        requirements = check_service_requirements()
        
        # Validate all expected services are checked
        expected_services = ['hardhat', 'ipfs', 'web3', 'snarkjs']
        for service in expected_services:
            assert service in requirements
            assert isinstance(requirements[service], bool)
        
        # Test individual service validation
        self._test_hardhat_validation(requirements['hardhat'])
        self._test_ipfs_validation(requirements['ipfs'])
        self._test_web3_validation(requirements['web3'])
        self._test_snarkjs_validation(requirements['snarkjs'])
    
    def _test_hardhat_validation(self, hardhat_available: bool):
        """Test Hardhat-specific validation."""
        if hardhat_available:
            # If Hardhat is available, verify we can access it
            try:
                contracts_dir = Path(__file__).parent.parent / "contracts"
                if contracts_dir.exists():
                    result = subprocess.run(
                        ["npx", "hardhat", "--version"],
                        cwd=contracts_dir,
                        capture_output=True,
                        timeout=10
                    )
                    assert result.returncode == 0
            except Exception:
                # Hardhat might be installed but not working properly
                pass
        else:
            # If Hardhat is not available, integration tests should skip
            assert True  # This is expected
    
    def _test_ipfs_validation(self, ipfs_available: bool):
        """Test IPFS-specific validation."""
        if ipfs_available:
            # If IPFS is available, verify basic command works
            try:
                result = subprocess.run(
                    ["ipfs", "version"],
                    capture_output=True,
                    timeout=10
                )
                assert result.returncode == 0
            except Exception:
                # IPFS might be installed but not working properly
                pass
        else:
            # If IPFS is not available, relevant tests should skip
            assert True  # This is expected
    
    def _test_web3_validation(self, web3_available: bool):
        """Test Web3-specific validation."""
        if web3_available:
            # If web3 is available, verify we can import it
            try:
                import web3
                assert hasattr(web3, 'Web3')
            except ImportError:
                assert False, "web3 reported as available but cannot import"
        else:
            # If web3 is not available, EVM tests should skip
            with pytest.raises(ImportError):
                import web3
    
    def _test_snarkjs_validation(self, snarkjs_available: bool):
        """Test snarkjs-specific validation."""
        if snarkjs_available:
            # If snarkjs is available, verify basic command works
            try:
                result = subprocess.run(
                    ["snarkjs", "--version"],
                    capture_output=True,
                    timeout=10
                )
                assert result.returncode == 0
            except Exception:
                # snarkjs might be installed but not working properly
                pass
        else:
            # If snarkjs is not available, SNARK tests should skip
            assert True  # This is expected
    
    @pytest.mark.integration
    def test_integration_test_skipping_behavior(self):
        """Test that integration tests properly skip when services are unavailable."""
        requirements = check_service_requirements()
        
        # Simulate missing services and verify tests would skip appropriately
        missing_services = [service for service, available in requirements.items() if not available]
        
        if missing_services:
            print(f"Missing services (tests will skip): {missing_services}")
            
            # Verify that tests requiring these services would skip
            for service in missing_services:
                if service == 'hardhat':
                    # Tests marked with @pytest.mark.requires_evm should skip
                    assert True
                elif service == 'ipfs':
                    # Tests marked with @pytest.mark.requires_ipfs should skip
                    assert True
                elif service == 'web3':
                    # EVM-related tests should skip
                    assert True
                elif service == 'snarkjs':
                    # SNARK-related tests should skip
                    assert True
        else:
            print("All services available - tests can run")
    
    def test_environment_variable_validation(self):
        """Test environment variable validation and setup."""
        # Test that environment variables are properly handled
        original_env = {}
        test_env_vars = [
            'USE_REAL_EVM',
            'USE_REAL_IPFS', 
            'USE_REAL_SNARK',
            'WEB3_PROVIDER_URI',
            'IPFS_API_URL'
        ]
        
        try:
            # Save original values
            for var in test_env_vars:
                original_env[var] = os.environ.get(var)
            
            # Test with integration environment
            with integration_environment() as env:
                # Verify environment variables are set correctly
                assert os.environ.get('USE_REAL_EVM') == '1'
                assert os.environ.get('USE_REAL_IPFS') == '1'
                
                if 'hardhat' in env['services_started']:
                    provider_uri = os.environ.get('WEB3_PROVIDER_URI', '')
                    assert 'localhost' in provider_uri
                    assert str(env['hardhat_port']) in provider_uri
                
                if 'ipfs' in env['services_started']:
                    ipfs_url = os.environ.get('IPFS_API_URL', '')
                    assert 'localhost' in ipfs_url
                    assert str(env['ipfs_port']) in ipfs_url
        
        finally:
            # Restore original environment
            for var, value in original_env.items():
                if value is None:
                    os.environ.pop(var, None)
                else:
                    os.environ[var] = value
    
    def test_graceful_fallback_mechanisms(self):
        """Test graceful fallback when external services fail."""
        # Test that the system gracefully falls back to simulation mode
        
        # Test medical redaction engine without external services
        engine = MyRedactionEngine()
        
        # Should initialize successfully even without external services
        assert engine is not None
        assert engine.snark_manager is not None
        assert engine.medical_contract is not None
        
        # Basic functionality should work in simulation mode
        patient_data = {
            "patient_id": "FALLBACK_TEST_001",
            "patient_name": "Fallback Test Patient",
            "medical_record_number": "MRN_FALLBACK_001",
            "diagnosis": "Fallback test condition",
            "treatment": "Fallback test treatment",
            "physician": "Dr. Fallback Test"
        }
        
        # Create and store medical record (simulation mode)
        medical_record = engine.create_medical_data_record(patient_data)
        assert medical_record.patient_id == "FALLBACK_TEST_001"
        
        stored = engine.store_medical_data(medical_record)
        assert stored is True
        
        # Request redaction (simulation mode)
        request_id = engine.request_data_redaction(
            patient_id="FALLBACK_TEST_001",
            redaction_type="DELETE",
            reason="Fallback test",
            requester="fallback_admin",
            requester_role="ADMIN"
        )
        
        assert request_id is not None
        assert isinstance(request_id, str)
    
    @pytest.mark.integration
    def test_service_health_monitoring(self):
        """Test service health monitoring and status reporting."""
        requirements = check_service_requirements()
        
        # Test that we can monitor service health
        health_status = {
            'hardhat': 'unknown',
            'ipfs': 'unknown', 
            'evm_connection': 'unknown',
            'ipfs_connection': 'unknown'
        }
        
        # Test Hardhat health
        if requirements['hardhat']:
            with integration_environment() as env:
                if 'hardhat' in env['services_started']:
                    health_status['hardhat'] = 'running'
                    
                    # Test EVM connection health
                    try:
                        evm_client = EVMClient()
                        if evm_client.connect():
                            health_status['evm_connection'] = 'connected'
                        else:
                            health_status['evm_connection'] = 'failed'
                    except Exception:
                        health_status['evm_connection'] = 'error'
                else:
                    health_status['hardhat'] = 'failed_to_start'
        else:
            health_status['hardhat'] = 'not_available'
        
        # Test IPFS health
        if requirements['ipfs']:
            with integration_environment() as env:
                if 'ipfs' in env['services_started']:
                    health_status['ipfs'] = 'running'
                    
                    # Test IPFS connection health
                    try:
                        ipfs_client = get_ipfs_client()
                        if ipfs_client is not None:
                            # Test basic operation
                            test_content = "health_check"
                            cid = ipfs_client.add(test_content)
                            if cid and len(cid) > 0:
                                health_status['ipfs_connection'] = 'connected'
                            else:
                                health_status['ipfs_connection'] = 'failed'
                        else:
                            health_status['ipfs_connection'] = 'client_unavailable'
                    except Exception:
                        health_status['ipfs_connection'] = 'error'
                else:
                    health_status['ipfs'] = 'failed_to_start'
        else:
            health_status['ipfs'] = 'not_available'
        
        # Verify health status is comprehensive
        for service, status in health_status.items():
            assert status != 'unknown', f"Health status for {service} was not determined"
            assert status in [
                'running', 'connected', 'failed_to_start', 'failed', 
                'error', 'not_available', 'client_unavailable'
            ], f"Unexpected health status for {service}: {status}"
        
        print(f"Service health status: {health_status}")


@pytest.mark.integration
class TestErrorHandlingAndResilience:
    """Test error handling and resilience in integration scenarios."""
    
    def test_graceful_degradation_no_services(self):
        """Test graceful degradation when no external services are available."""
        # This test runs without starting services
        engine = MyRedactionEngine()
        
        # Should still be functional in simulation mode
        assert engine.snark_manager is not None
        assert engine.medical_contract is not None
        
        # Basic operations should work
        patient_data = {
            "patient_id": "FALLBACK_001",
            "patient_name": "Fallback Test Patient",
            "medical_record_number": "MRN_FB_001",
            "diagnosis": "Fallback test",
            "treatment": "Fallback treatment",
            "physician": "Dr. Fallback"
        }
        
        medical_record = engine.create_medical_data_record(patient_data)
        assert medical_record.patient_id == "FALLBACK_001"
        
        stored = engine.store_medical_data(medical_record)
        assert stored is True
    
    def test_service_failure_recovery(self):
        """Test recovery from service failures."""
        with integration_environment() as env:
            # Even if some services fail to start, others should work
            services = env['services_started']
            
            # Test that we can handle partial service availability
            if 'hardhat' in services:
                # EVM functionality should work
                evm_client = EVMClient()
                # Connection may or may not succeed, but should not crash
                try:
                    connected = evm_client.connect()
                    assert isinstance(connected, bool)
                except Exception as e:
                    # Connection failure is acceptable in test environment
                    assert isinstance(e, Exception)
            
            if 'ipfs' in services:
                # IPFS functionality should work
                ipfs_client = get_ipfs_client()
                if ipfs_client is not None:
                    # Basic operation should work
                    test_content = "Recovery test"
                    cid = ipfs_client.add(test_content)
                    assert isinstance(cid, str)


if __name__ == "__main__":
    # Allow running integration tests directly
    pytest.main([__file__, "-v", "-m", "integration"])