# Node.js Requirements for MedChain

This file documents the Node.js dependencies required for full MedChain functionality.

## Required Global Dependencies

### snarkjs (v0.7.5)

**Purpose**: Zero-knowledge SNARK proof generation and verification
**Installation**: `npm install -g snarkjs@0.7.5`
**Usage**: Used by `adapters/snark.py` for real SNARK proof generation

### circom (latest)

**Purpose**: Compiling zero-knowledge circuits
**Installation**: Download from <https://github.com/iden3/circom/releases>
**Usage**: Compiles `.circom` files to `.wasm` and `.r1cs` for SNARK proofs

## Development Dependencies

### Hardhat Ecosystem

- `hardhat@^2.22.5` - Ethereum development framework
- `@nomicfoundation/hardhat-toolbox@^4.0.0` - Hardhat plugin collection
- `solidity-coverage@^0.8.16` - Solidity code coverage

### Additional Tools

- `snarkjs@^0.7.5` (also in contracts/package.json for local builds)

## Installation Commands

```bash
# Quick setup (all dependencies)
npm run setup

# Manual installation
npm install -g snarkjs@0.7.5

# Install circom (Linux x64)
wget -O /tmp/circom https://github.com/iden3/circom/releases/latest/download/circom-linux-amd64
sudo mv /tmp/circom /usr/local/bin/circom
sudo chmod +x /usr/local/bin/circom

# Install project dependencies
npm install
cd contracts && npm install
```

## Verification

```bash
# Verify installations
snarkjs --version   # Should show v0.7.5
circom --version    # Should show version info
node --version      # Should be >= 16.0.0
npm --version       # Should be >= 8.0.0
```

## Environment Variables

```bash
# Enable real SNARK functionality
USE_REAL_SNARK=1

# Circuit directory (default: circuits)
CIRCUITS_DIR=circuits

# Enable real EVM functionality
USE_REAL_EVM=1
WEB3_PROVIDER_URI=http://localhost:8545

# Enable real IPFS functionality  
USE_REAL_IPFS=1
IPFS_API_URL=http://localhost:5001
```

## Troubleshooting

### snarkjs command not found

- Ensure global installation: `npm install -g snarkjs`
- Check PATH includes npm global bin: `npm bin -g`

### circom command not found

- Download binary from GitHub releases
- Ensure executable permissions: `chmod +x /usr/local/bin/circom`
- Alternative: Install via Rust cargo

### Circuit compilation fails

- Ensure circuit artifacts exist: `ls circuits/build/`
- Run build process: `npm run build-circuits`
- Check Powers of Tau file: `ls tools/powersOfTau28_hez_final_*.ptau`

### SNARK proof generation fails

- Verify snarkjs installation: `snarkjs --version`
- Check circuit inputs match expected format
- Ensure witness generation works: Test with `circuits/input/example.json`
