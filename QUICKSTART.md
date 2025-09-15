# Quick Start Guide

This guide will get you up and running with the MedChain project in minutes.

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git**

## One-Command Setup

```bash
# Clone and setup everything in one go
git clone <your-repo-url>
cd medchain-avitabile
make setup
```

This will:

1. Install global npm packages (snarkjs, circom)
2. Install local npm dependencies
3. Install Python dependencies

## Alternative Setup

If you prefer manual control:

```bash
# Install Node.js dependencies
make setup-npm

# Install Python dependencies  
make setup-python
```

## Verify Installation

```bash
# Check SNARK tools
snarkjs --version
circom --version

# Check Python environment
python -c "import CH.ChameleonHash; print('Python deps OK')"

# Run a quick test
python -m pytest tests/ -k "test_basic" -v
```

## Common Commands

```bash
# Compile smart contracts
make contracts-compile

# Compile ZK circuits
make circuits-compile

# Run IPFS integration
make ipfs-docker-up
make ipfs-test

# Run demos
python demo/medchain_demo.py
python demo/avitabile_redaction_demo.py
```

## Project Structure

- `adapters/` - Protocol adapters (IPFS, EVM, SNARK)
- `medical/` - Medical data handling and redaction
- `contracts/` - Smart contracts (Hardhat project)
- `circuits/` - Zero-knowledge circuits (Circom)
- `CH/` - Chameleon hash implementation
- `demo/` - Example usage scripts
- `tests/` - Test suite

## Need Help?

- Check [`README.md`](README.md) for detailed setup instructions
- See [`docs/NODEJS_REQUIREMENTS.md`](docs/NODEJS_REQUIREMENTS.md) for Node.js specifics
- Review [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) for architecture details
- Run `make help` for all available commands

## Key Features

- ✅ Real SNARK proof generation with snarkjs
- ✅ Hybrid simulation/real proof modes
- ✅ IPFS content addressing
- ✅ Smart contract integration
- ✅ Medical data redaction
- ✅ Comprehensive test suite
