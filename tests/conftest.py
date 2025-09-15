"""
Integration Test Infrastructure
==============================

This module provides infrastructure for integration tests that require real external services:
- Hardhat devnet for EVM functionality
- IPFS daemon for storage
- Contract deployment and interaction
- End-to-end workflows

Usage:
    pytest -m integration  # Run only integration tests
    pytest -m "not integration"  # Skip integration tests
    pytest tests/test_integration.py -v  # Run specific integration tests
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import threading
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from adapters.config import env_bool, env_str
from adapters.evm import EVMClient
from adapters.ipfs import get_ipfs_client


class ServiceManager:
    """Manages external services for integration tests."""
    
    def __init__(self):
        self.hardhat_process = None
        self.ipfs_process = None
        self.hardhat_port = None
        self.ipfs_port = None
        self.contracts_deployed = False
        self.deployment_addresses = {}
        
    def find_free_port(self, start_port: int = 8545) -> int:
        """Find a free port starting from the given port."""
        for port in range(start_port, start_port + 100):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return port
                except OSError:
                    continue
        raise RuntimeError(f"No free port found starting from {start_port}")
    
    def start_hardhat_node(self) -> bool:
        """Start Hardhat node for EVM testing."""
        try:
            # Find free port
            self.hardhat_port = self.find_free_port(8545)
            
            contracts_dir = project_root / "contracts"
            if not contracts_dir.exists():
                print(f"Contracts directory not found: {contracts_dir}")
                return False
            
            # Start Hardhat node
            cmd = ["npx", "hardhat", "node", "--port", str(self.hardhat_port)]
            self.hardhat_process = subprocess.Popen(
                cmd,
                cwd=contracts_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for node to start
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    # Test connection
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        result = s.connect_ex(('localhost', self.hardhat_port))
                        if result == 0:
                            print(f"Hardhat node started on port {self.hardhat_port}")
                            return True
                except:
                    pass
                time.sleep(1)
            
            print("Failed to start Hardhat node")
            self.stop_hardhat_node()
            return False
            
        except Exception as e:
            print(f"Error starting Hardhat node: {e}")
            return False
    
    def stop_hardhat_node(self):
        """Stop Hardhat node."""
        if self.hardhat_process:
            try:
                self.hardhat_process.terminate()
                self.hardhat_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.hardhat_process.kill()
                self.hardhat_process.wait()
            except:
                pass
            self.hardhat_process = None
            self.hardhat_port = None
    
    def start_ipfs_daemon(self) -> bool:
        """Start IPFS daemon for testing."""
        try:
            # Check if IPFS is available
            result = subprocess.run(
                ["ipfs", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print("IPFS not available")
                return False
            
            # Find free port for IPFS API
            self.ipfs_port = self.find_free_port(5001)
            
            # Create temporary IPFS repository
            with tempfile.TemporaryDirectory() as temp_repo:
                env = os.environ.copy()
                env['IPFS_PATH'] = temp_repo
                
                # Initialize repository
                subprocess.run(
                    ["ipfs", "init"],
                    env=env,
                    capture_output=True,
                    timeout=30
                )
                
                # Configure API port
                subprocess.run([
                    "ipfs", "config", "Addresses.API", f"/ip4/127.0.0.1/tcp/{self.ipfs_port}"
                ], env=env, capture_output=True)
                
                # Start daemon
                self.ipfs_process = subprocess.Popen(
                    ["ipfs", "daemon"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for daemon to start
                max_attempts = 30
                for attempt in range(max_attempts):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(1)
                            result = s.connect_ex(('localhost', self.ipfs_port))
                            if result == 0:
                                print(f"IPFS daemon started on port {self.ipfs_port}")
                                return True
                    except:
                        pass
                    time.sleep(1)
            
            print("Failed to start IPFS daemon")
            self.stop_ipfs_daemon()
            return False
            
        except Exception as e:
            print(f"Error starting IPFS daemon: {e}")
            return False
    
    def stop_ipfs_daemon(self):
        """Stop IPFS daemon."""
        if self.ipfs_process:
            try:
                self.ipfs_process.terminate()
                self.ipfs_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.ipfs_process.kill()
                self.ipfs_process.wait()
            except:
                pass
            self.ipfs_process = None
            self.ipfs_port = None
    
    def deploy_contracts(self) -> bool:
        """Deploy contracts to the running Hardhat node."""
        try:
            contracts_dir = project_root / "contracts"
            
            # Set environment for deployment
            env = os.environ.copy()
            env['WEB3_PROVIDER_URI'] = f"http://localhost:{self.hardhat_port}"
            
            # Run deployment script
            result = subprocess.run(
                ["npx", "hardhat", "run", "scripts/deploy.js", "--network", "localhost"],
                cwd=contracts_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Parse deployment addresses from output
                try:
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if "deployed at:" in line.lower():
                            if "MedicalDataManager" in line:
                                address = line.split("deployed at:")[-1].strip()
                                self.deployment_addresses['MedicalDataManager'] = address
                            elif "RedactionVerifier" in line:
                                address = line.split("deployed at:")[-1].strip()
                                self.deployment_addresses['RedactionVerifier'] = address
                    
                    # Also try to read from deployed_addresses.json
                    deployed_file = contracts_dir / "deployed_addresses.json"
                    if deployed_file.exists():
                        with open(deployed_file) as f:
                            deployed_data = json.load(f)
                            for name, info in deployed_data.items():
                                if isinstance(info, dict) and 'address' in info:
                                    self.deployment_addresses[name] = info['address']
                    
                    self.contracts_deployed = True
                    print(f"Contracts deployed: {self.deployment_addresses}")
                    return True
                except Exception as e:
                    print(f"Error parsing deployment output: {e}")
                    print(f"Stdout: {result.stdout}")
                    
            else:
                print(f"Deployment failed: {result.stderr}")
            
            return False
            
        except Exception as e:
            print(f"Error deploying contracts: {e}")
            return False
    
    def get_web3_uri(self) -> Optional[str]:
        """Get Web3 provider URI."""
        if self.hardhat_port:
            return f"http://localhost:{self.hardhat_port}"
        return None
    
    def get_ipfs_api_url(self) -> Optional[str]:
        """Get IPFS API URL."""
        if self.ipfs_port:
            return f"http://localhost:{self.ipfs_port}"
        return None
    
    def cleanup(self):
        """Clean up all services."""
        self.stop_hardhat_node()
        self.stop_ipfs_daemon()
        self.contracts_deployed = False
        self.deployment_addresses.clear()


# Global service manager instance
_service_manager = ServiceManager()


def check_service_requirements() -> Dict[str, bool]:
    """Check which services are available for testing."""
    requirements = {
        'hardhat': False,
        'ipfs': False,
        'web3': False,
        'snarkjs': False
    }
    
    try:
        # Check Hardhat
        result = subprocess.run(
            ["npx", "hardhat", "--version"],
            capture_output=True,
            timeout=10,
            cwd=project_root / "contracts"
        )
        requirements['hardhat'] = result.returncode == 0
    except:
        pass
    
    try:
        # Check IPFS
        result = subprocess.run(
            ["ipfs", "version"],
            capture_output=True,
            timeout=10
        )
        requirements['ipfs'] = result.returncode == 0
    except:
        pass
    
    try:
        # Check web3
        import web3
        requirements['web3'] = True
    except ImportError:
        pass
    
    try:
        # Check snarkjs
        result = subprocess.run(
            ["snarkjs", "--version"],
            capture_output=True,
            timeout=10
        )
        requirements['snarkjs'] = result.returncode == 0
    except:
        pass
    
    return requirements


@contextmanager
def integration_environment():
    """Context manager for integration test environment."""
    try:
        # Start services
        services_started = []
        
        if _service_manager.start_hardhat_node():
            services_started.append('hardhat')
            if _service_manager.deploy_contracts():
                services_started.append('contracts')
        
        if _service_manager.start_ipfs_daemon():
            services_started.append('ipfs')
        
        # Set environment variables
        old_env = {}
        new_env = {
            'USE_REAL_EVM': '1',
            'USE_REAL_IPFS': '1',
            'WEB3_PROVIDER_URI': _service_manager.get_web3_uri() or '',
            'IPFS_API_URL': _service_manager.get_ipfs_api_url() or ''
        }
        
        for key, value in new_env.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        yield {
            'services_started': services_started,
            'hardhat_port': _service_manager.hardhat_port,
            'ipfs_port': _service_manager.ipfs_port,
            'deployment_addresses': _service_manager.deployment_addresses.copy(),
            'service_manager': _service_manager
        }
        
    finally:
        # Restore environment
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # Cleanup services
        _service_manager.cleanup()


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "requires_evm: mark test as requiring EVM node"
    )
    config.addinivalue_line(
        "markers", "requires_ipfs: mark test as requiring IPFS daemon"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration tests."""
    skip_integration = pytest.mark.skip(reason="Integration tests require external services")
    
    for item in items:
        if "integration" in item.keywords:
            # Check if we should skip integration tests
            if config.getoption("-m") and "not integration" in config.getoption("-m"):
                item.add_marker(skip_integration)