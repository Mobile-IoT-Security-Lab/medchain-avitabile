"""EVM adapter scaffold.

Provides a minimal interface; real implementation uses web3.py when enabled.
Safe to import without web3 installed; imports are deferred.

### Bookmark2 for next meeting - Phase 2 on-chain verification implementation
"""
from __future__ import annotations

from typing import Any, Optional
from .config import env_bool, env_str
import json, os

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

    def setRequireProofs(self, contract, value: bool) -> Optional[str]:
        if not self._connected:
            return None
        fn = contract.functions.setRequireProofs(bool(value))
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

    # -------- Groth16 support (snarkjs) --------
    def _parse_groth16_calldata(self, proof_json_path: str, public_json_path: str):
        with open(proof_json_path, "r") as f:
            proof = json.load(f)
        with open(public_json_path, "r") as f:
            pub = json.load(f)

        # snarkjs proof.json uses decimal strings
        def to_int(x):
            return int(x)

        pi_a = proof.get("pi_a", [])
        pi_b = proof.get("pi_b", [])
        pi_c = proof.get("pi_c", [])
        if not (isinstance(pi_a, list) and isinstance(pi_b, list) and isinstance(pi_c, list)):
            raise ValueError("Invalid proof.json structure")
        # Take first two limbs (drop the last 1)
        pA = [to_int(pi_a[0]), to_int(pi_a[1])]
        # For G2, snarkjs proof.json stores Fp2 limbs as [[bx0, bx1],[by0, by1],[1,0]]
        # Solidity calldata expects swapped limbs: [[bx1, bx0],[by1, by0]]
        pB = [
            [to_int(pi_b[0][1]), to_int(pi_b[0][0])],
            [to_int(pi_b[1][1]), to_int(pi_b[1][0])],
        ]
        pC = [to_int(pi_c[0]), to_int(pi_c[1])]
        # Public signals array
        if not isinstance(pub, list) or len(pub) < 1:
            raise ValueError("Invalid public.json structure")
        pubSignals = [to_int(pub[0])]
        return pA, pB, pC, pubSignals

    def requestDataRedactionWithGroth16Proof(
        self,
        contract,
        patient_id: str,
        redaction_type: str,
        reason: str,
        pA: list[int],
        pB: list[list[int]],
        pC: list[int],
        pubSignals: list[int],
    ) -> Optional[str]:
        if not self._connected:
            return None
        fn = contract.functions.requestDataRedactionWithGroth16Proof(
            patient_id, redaction_type, reason, pA, pB, pC, pubSignals
        )
        return self._build_and_send(fn)

    def requestDataRedactionFromSnarkjs(
        self,
        contract,
        patient_id: str,
        redaction_type: str,
        reason: str,
        proof_json_path: Optional[str] = None,
        public_json_path: Optional[str] = None,
    ) -> Optional[str]:
        if not self._connected:
            return None
        proof_path = proof_json_path or env_str("GROTH16_PROOF_JSON", "circuits/build/proof.json")
        public_path = public_json_path or env_str("GROTH16_PUBLIC_JSON", "circuits/build/public.json")
        if not (proof_path and public_path and os.path.exists(proof_path) and os.path.exists(public_path)):
            return None
        try:
            pA, pB, pC, pubSignals = self._parse_groth16_calldata(proof_path, public_path)
        except Exception:
            return None
        return self.requestDataRedactionWithGroth16Proof(
            contract, patient_id, redaction_type, reason, pA, pB, pC, pubSignals
        )

    def requestDataRedactionAuto(
        self,
        contract,
        patient_id: str,
        redaction_type: str,
        reason: str,
        proof_json_path: Optional[str] = None,
        public_json_path: Optional[str] = None,
    ) -> Optional[str]:
        if not self._connected:
            return None
        tx = self.requestDataRedactionFromSnarkjs(
            contract, patient_id, redaction_type, reason, proof_json_path, public_json_path
        )
        if tx:
            return tx
        return None

    def approveRedaction(self, contract, request_id: int) -> Optional[str]:
        if not self._connected:
            return None
        fn = contract.functions.approveRedaction(int(request_id))
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
        # Hardhat artifact path convention (project uses sources under src/)
        p1 = f"{self._artifacts_dir}/contracts/{contract_name}.sol/{contract_name}.json"
        p2 = f"{self._artifacts_dir}/src/{contract_name}.sol/{contract_name}.json"
        return p1 if os.path.exists(p1) else p2

    def _load_artifact(self, contract_name: str) -> Optional[dict]:
        import json, os
        path = self._artifact_path(contract_name)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    # Deployed addresses helpers
    def _contracts_root(self) -> str:
        # Resolve repo root relative to this file
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(here, os.pardir, "contracts"))

    def _load_deployed_address(self, contract_name: str) -> Optional[str]:
        # Try consolidated file first
        root = self._contracts_root()
        consolidated = os.path.join(root, "deployed_addresses.json")
        try:
            if os.path.exists(consolidated):
                with open(consolidated, "r") as f:
                    data = json.load(f)
                entry = data.get(contract_name)
                if isinstance(entry, dict) and entry.get("address"):
                    return entry.get("address")
        except Exception:
            pass
        # Try per-chain deployments directory
        deployments_dir = os.path.join(root, "deployments")
        if not os.path.isdir(deployments_dir):
            return None
        try:
            for chainId in os.listdir(deployments_dir):
                cdir = os.path.join(deployments_dir, chainId)
                if not os.path.isdir(cdir):
                    continue
                fpath = os.path.join(cdir, f"{contract_name}.json")
                if os.path.exists(fpath):
                    with open(fpath, "r") as f:
                        data = json.load(f)
                    addr = data.get("address")
                    if addr:
                        return addr
        except Exception:
            return None
        return None

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

    def load_contract(self, contract_name: str, address: Optional[str] = None) -> Optional[Any]:
        if not self._connected or Web3 is None:
            return None
        art = self._load_artifact(contract_name)
        if not art:
            return None
        addr = address or self._load_deployed_address(contract_name)
        if not addr:
            return None
        return self._w3.eth.contract(address=addr, abi=art.get("abi"))

def get_evm_client() -> Optional[EVMClient]:
    client = EVMClient()
    if not client.is_enabled():
        return None
    if not client.connect():
        return None
    return client
