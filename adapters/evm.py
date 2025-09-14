"""EVM adapter scaffold.

Provides a minimal interface; real implementation uses web3.py when enabled.
Safe to import without web3 installed; imports are deferred.
"""
from __future__ import annotations

from typing import Any, Optional
from .config import env_bool, env_str

try:  # optional dependency
    from web3 import Web3  # type: ignore
    from web3.middleware import geth_poa_middleware  # type: ignore
except Exception:  # pragma: no cover - optional import
    Web3 = None  # type: ignore
    geth_poa_middleware = None  # type: ignore


class EVMClient:
    """Placeholder EVM client. Wire up in a later step.

    Intended methods:
      - connect(provider_url)
      - deploy_medical_contract(...)
      - load_contract(abi, address)
      - storeMedicalData(...)
      - requestDataRedaction(...)
      - approveRedaction(...)
      - executeRedaction(...)
    """

    def __init__(self) -> None:
        self._connected = False
        self._w3 = None
        self._acct = None
        self._artifacts_dir = env_str("CONTRACT_ARTIFACTS_DIR", "contracts/artifacts")

    def is_enabled(self) -> bool:
        return env_bool("USE_REAL_EVM", False)

    def connect(self) -> bool:
        if not self.is_enabled() or Web3 is None:
            return False
        provider = env_str("WEB3_PROVIDER_URI", "http://127.0.0.1:8545")
        w3 = Web3(Web3.HTTPProvider(provider))
        if geth_poa_middleware is not None:
            try:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except Exception:
                pass
        if not w3.is_connected():  # web3>=6
            return False
        pk = env_str("EVM_PRIVATE_KEY")
        if pk:
            self._acct = w3.eth.account.from_key(pk)
        self._w3 = w3
        self._connected = True
        return True

    # Minimal placeholders for higher-level calls
    def _build_and_send(self, fn) -> Optional[str]:
        if not self._connected or self._w3 is None:
            return None
        try:
            tx = fn.build_transaction({
                "from": (self._acct.address if self._acct else self._w3.eth.accounts[0]),
                "nonce": self._w3.eth.get_transaction_count(self._acct.address if self._acct else self._w3.eth.accounts[0]),
                "chainId": int(env_str("EVM_CHAIN_ID", "31337")),
                # gas and gasPrice can be estimated; keep simple defaults
                "gas": 3_000_000,
            })
            if self._acct is not None:
                signed = self._w3.eth.account.sign_transaction(tx, self._acct.key)
                tx_hash = self._w3.eth.send_raw_transaction(signed.rawTransaction)
            else:
                tx_hash = self._w3.eth.send_transaction(tx)
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.transactionHash.hex()
        except Exception:
            return None

    def storeMedicalData(self, contract, patient_id: str, ipfs_hash: str, ciphertext_hash: bytes) -> Optional[str]:
        if not self._connected:
            return None
        # ciphertext_hash must be 32 bytes
        if not isinstance(ciphertext_hash, (bytes, bytearray)) or len(ciphertext_hash) != 32:
            return None
        fn = contract.functions.storeMedicalData(patient_id, ipfs_hash, ciphertext_hash)
        return self._build_and_send(fn)

    def requestDataRedaction(self, contract, patient_id: str, redaction_type: str, reason: str) -> Optional[str]:
        if not self._connected:
            return None
        fn = contract.functions.requestDataRedaction(patient_id, redaction_type, reason)
        return self._build_and_send(fn)

    def setVerifier(self, contract, verifier_address: str) -> Optional[str]:
        if not self._connected:
            return None
        fn = contract.functions.setVerifier(verifier_address)
        return self._build_and_send(fn)

    def requestDataRedactionWithProof(
        self,
        contract,
        patient_id: str,
        redaction_type: str,
        reason: str,
        proof: bytes,
        policy_hash: bytes,
        merkle_root: bytes,
        original_hash: bytes,
        redacted_hash: bytes,
    ) -> Optional[str]:
        if not self._connected:
            return None
        fn = contract.functions.requestDataRedactionWithProof(
            patient_id, redaction_type, reason, proof, policy_hash, merkle_root, original_hash, redacted_hash
        )
        return self._build_and_send(fn)

    # Events
    def get_events(self, contract, event_name: str, from_block: int = 0, to_block: str | int = "latest") -> list:
        if not self._connected:
            return []
        try:
            event_abi = getattr(contract.events, event_name)
            logs = event_abi().get_logs(fromBlock=from_block, toBlock=to_block)
            return logs
        except Exception:
            return []

    # Artifacts and deployment
    def _artifact_path(self, contract_name: str) -> str:
        # Hardhat artifact path convention
        return f"{self._artifacts_dir}/contracts/{contract_name}.sol/{contract_name}.json"

    def _load_artifact(self, contract_name: str) -> Optional[dict]:
        import json, os
        path = self._artifact_path(contract_name)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def deploy(self, contract_name: str, args: Optional[list] = None) -> Optional[tuple[str, Any]]:
        if not self._connected or Web3 is None:
            return None
        art = self._load_artifact(contract_name)
        if not art:
            return None
        abi = art.get("abi")
        bytecode = art.get("bytecode")
        if not abi or not bytecode:
            return None
        Contract = self._w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = Contract.constructor(*(args or [])).build_transaction({
            "from": (self._acct.address if self._acct else self._w3.eth.accounts[0]),
            "nonce": self._w3.eth.get_transaction_count(self._acct.address if self._acct else self._w3.eth.accounts[0]),
            "chainId": int(env_str("EVM_CHAIN_ID", "31337")),
            "gas": 6_000_000,
        })
        if self._acct is not None:
            signed = self._w3.eth.account.sign_transaction(tx, self._acct.key)
            tx_hash = self._w3.eth.send_raw_transaction(signed.rawTransaction)
        else:
            tx_hash = self._w3.eth.send_transaction(tx)
        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        address = receipt.contractAddress
        contract = self._w3.eth.contract(address=address, abi=abi)
        return address, contract

    def load_contract(self, contract_name: str, address: str) -> Optional[Any]:
        if not self._connected or Web3 is None:
            return None
        art = self._load_artifact(contract_name)
        if not art:
            return None
        return self._w3.eth.contract(address=address, abi=art.get("abi"))

def get_evm_client() -> Optional[EVMClient]:
    client = EVMClient()
    if not client.is_enabled():
        return None
    if not client.connect():
        return None
    return client
