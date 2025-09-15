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
# RECOMMENDED: My medical demo with clear before/after states
python demo/my_medical_demo.py

# Original demos
python demo/medchain_demo.py
python demo/avitabile_redaction_demo.py
python demo/before_after_redaction_demo.py
python demo/medical_redaction_demo.py
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

- Real SNARK proof generation with snarkjs
- Hybrid simulation/real proof modes
- IPFS content addressing
- Smart contract integration
- Medical data redaction
- Comprehensive test suite

## My Medical Demo Highlights

The **my_medical_demo.py** is specifically designed for academic presentations and clearly demonstrates all three redaction types from the paper "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains":

### DELETE Redaction (GDPR Article 17)

- Shows complete patient data removal
- Demonstrates "Right to be Forgotten" compliance
- Clear before: full patient record → after: record not found

### MODIFY Redaction (Medical Corrections)

- Shows medical data correction workflow
- Physician-initiated diagnosis correction
- Clear before: incorrect diagnosis → after: corrected diagnosis

### ANONYMIZE Redaction (HIPAA Research)

- Shows research data anonymization
- Multi-party ethics approval process  
- Clear before: identifiable data → after: anonymized for research

Each demonstration includes:

- Detailed medical record before/after states
- SNARK proof generation and verification
- Multi-party approval workflows (IRB, Privacy Officer, etc.)
- Compliance verification (GDPR, HIPAA)
- Complete audit trail and blockchain state changes
