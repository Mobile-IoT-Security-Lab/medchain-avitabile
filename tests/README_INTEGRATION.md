# Integration Test Suite

This directory contains comprehensive integration tests for the Medchain Avitabile project that test interactions with real external services.

## Overview

The integration test suite validates:

- **Service Integration**: IPFS daemon, Hardhat devnet, EVM contracts
- **End-to-End Workflows**: Complete redaction pipelines from data storage to proof verification
- **Environment Validation**: Graceful degradation when services are unavailable
- **Cross-Component Testing**: IPFS ↔ EVM integration, SNARK proof generation/verification

## Running Integration Tests

### Run All Integration Tests

```bash
pytest -m integration tests/test_integration.py -v
```

### Run Specific Test Categories

```bash
# Service requirement tests (always run)
pytest tests/test_integration.py::TestServiceRequirements -v

# Environment validation tests 
pytest tests/test_integration.py::TestEnvironmentValidation -v

# Devnet infrastructure tests (requires Hardhat)
pytest -m "integration and requires_evm" tests/test_integration.py -v

# IPFS integration tests (requires IPFS daemon)
pytest -m "integration and requires_ipfs" tests/test_integration.py -v

# Complete E2E workflow tests (requires all services)
pytest -m "integration and e2e" tests/test_integration.py -v
```

### Skip Integration Tests

```bash
# Run all tests except integration tests
pytest -m "not integration"
```

## Prerequisites

### Required Services

- **Hardhat**: For EVM devnet functionality

  ```bash
  cd contracts && npm install
  npx hardhat --version
  ```

- **IPFS**: For distributed storage testing

  ```bash
  ipfs version
  # Start daemon: ipfs daemon
  ```

- **Web3**: For EVM interaction

  ```bash
  pip install web3>=6
  ```

- **snarkjs**: For SNARK proof generation (optional)

  ```bash
  npm install -g snarkjs
  snarkjs --version
  ```

### Environment Variables

Integration tests automatically configure environment variables:

- `USE_REAL_EVM=1`: Enable real EVM backend
- `USE_REAL_IPFS=1`: Enable real IPFS backend  
- `WEB3_PROVIDER_URI`: Set to local Hardhat node
- `IPFS_API_URL`: Set to local IPFS daemon

## Test Architecture

### Service Management (`conftest.py`)

- **ServiceManager**: Handles lifecycle of external services
- **Port Discovery**: Automatically finds free ports for services
- **Environment Context**: Sets up isolated test environments
- **Graceful Cleanup**: Ensures services are properly stopped

### Test Categories

#### 1. Service Requirements (`TestServiceRequirements`)

- Validates service availability and requirements
- Always runs regardless of service availability
- Provides baseline functionality verification

#### 2. Devnet Infrastructure (`TestDevnetInfrastructure`)

- Tests Hardhat node startup/shutdown
- Tests IPFS daemon lifecycle management
- Validates service health and connectivity

#### 3. Contract Deployment (`TestContractDeployment`)

- Tests automated contract deployment to devnet
- Validates deployment address parsing and storage
- Tests EVM client contract loading

#### 4. IPFS Integration (`TestIPFSIntegration`)

- Tests real IPFS client operations
- Validates medical data IPFS storage/retrieval
- Tests encryption and content integrity

#### 5. End-to-End Workflows (`TestEndToEndWorkflow`)

- **Complete E2E Redaction**: Full workflow from data storage through redaction to proof verification
- **IPFS → EVM Integration**: Cross-component data flow testing
- **Proof Verification**: SNARK proof generation and validation

#### 6. Environment Validation (`TestEnvironmentValidation`)

- Comprehensive service requirement validation
- Environment variable handling verification
- Graceful fallback mechanism testing
- Service health monitoring

## Integration Test Features

### Automatic Service Discovery

- Tests automatically detect available services
- Gracefully skip tests when services are unavailable
- Provide clear feedback on missing dependencies

### Isolated Test Environments

- Each test runs in isolated environment with dedicated ports
- Automatic cleanup prevents service conflicts
- Environment variables are properly scoped

### Comprehensive E2E Testing

```python
# Example E2E test flow:
1. Start IPFS daemon and Hardhat node
2. Deploy smart contracts 
3. Upload original medical data to IPFS
4. Create redaction request with SNARK proof
5. Generate redacted version and upload to IPFS
6. Update on-chain pointer to redacted version
7. Verify complete workflow integrity
```

### Error Handling and Resilience

- Tests handle partial service availability
- Graceful degradation to simulation mode
- Comprehensive error reporting and debugging info

## Pytest Markers

- `@pytest.mark.integration`: All integration tests
- `@pytest.mark.requires_evm`: Tests requiring Hardhat/EVM
- `@pytest.mark.requires_ipfs`: Tests requiring IPFS daemon
- `@pytest.mark.requires_snark`: Tests requiring SNARK tools
- `@pytest.mark.e2e`: End-to-end workflow tests
- `@pytest.mark.slow`: Long-running tests

## Troubleshooting

### Common Issues

1. **Port conflicts**: Integration tests automatically find free ports
2. **Service not starting**: Check service prerequisites and logs
3. **Tests skipping**: Normal behavior when services unavailable
4. **Timeout errors**: Increase test timeout in pytest configuration

### Debug Mode

```bash
# Run with detailed output
pytest tests/test_integration.py -v -s --tb=long

# Run single test with full debugging
pytest tests/test_integration.py::TestEndToEndWorkflow::test_complete_e2e_redaction_workflow -v -s
```

### Service Health Check

```bash
# Verify service requirements
python -c "from tests.conftest import check_service_requirements; print(check_service_requirements())"
```

## Development Guidelines

### Adding New Integration Tests

1. Mark with appropriate `@pytest.mark.integration` and service markers
2. Use `integration_environment()` context manager for service setup
3. Include proper service requirement checks and graceful skipping
4. Test both success and failure scenarios
5. Ensure proper cleanup in test teardown

### Service Integration Patterns

```python
@pytest.mark.integration
@pytest.mark.requires_ipfs
def test_new_ipfs_functionality(self):
    requirements = check_service_requirements()
    if not requirements['ipfs']:
        pytest.skip("IPFS not available")
    
    with integration_environment() as env:
        if 'ipfs' not in env['services_started']:
            pytest.skip("IPFS daemon not started")
        
        # Test implementation here
```

## Performance Considerations

- Integration tests are slower than unit tests (30s-5min per test)
- Services are started fresh for each test context
- Use `pytest -x` to stop on first failure for faster debugging
- Consider running integration tests separately in CI/CD pipelines

## Continuous Integration

Integration tests are designed to run in CI environments:

- Automatically skip when services unavailable
- Provide clear success/skip/failure reporting
- Include performance benchmarking and timeout handling
- Generate comprehensive test reports and logs
