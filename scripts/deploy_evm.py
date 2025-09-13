#!/usr/bin/env python3
"""Deploy helper for EVM contracts using web3.py and local artifacts.

Prereqs:
- Hardhat artifacts in contracts/artifacts (run `npm i && npx hardhat compile` under contracts/)
- Env: WEB3_PROVIDER_URI, EVM_PRIVATE_KEY, EVM_CHAIN_ID

Usage:
    python scripts/deploy_evm.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from adapters.evm import get_evm_client
from adapters.config import env_str


def main():
    client = get_evm_client()
    if client is None:
        print("EVM client not available. Ensure USE_REAL_EVM=1 and web3 configured.")
        return 1

    # Deploy verifier first
    v = client.deploy("RedactionVerifier")
    if not v:
        print("Failed to deploy RedactionVerifier. Did you compile artifacts?")
        return 2
    verifier_addr, verifier = v
    print("RedactionVerifier:", verifier_addr)

    # Deploy manager
    m = client.deploy("MedicalDataManager")
    if not m:
        print("Failed to deploy MedicalDataManager. Did you compile artifacts?")
        return 3
    manager_addr, manager = m
    print("MedicalDataManager:", manager_addr)

    # Wire verifier
    txh = client.setVerifier(manager, verifier_addr)
    print("setVerifier tx:", txh)

    print("Export env to reuse:")
    print(f"export MEDICAL_CONTRACT_ADDRESS={manager_addr}")
    print(f"export VERIFIER_CONTRACT_ADDRESS={verifier_addr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

