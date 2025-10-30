"""EVM adapter scaffold.

Provides a minimal interface; real implementation uses web3.py when enabled.
Safe to import without web3 installed; imports are deferred.

### Bookmark2 for next meeting - Phase 2 on-chain verification implementation
"""
from __future__ import annotations

from typing import Any, Optional, Dict
from .config import env_bool, env_str
import json, os, time

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
    def _ensure_connection(self) -> bool:
        if self._connected:
            return True
        return self.connect()

    def _build_and_send(self, fn, *, return_receipt: bool = False):
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
            if return_receipt:
                return receipt
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

    # -------- Medical data helpers for integration tests --------
    def _get_medical_manager(self):
        if not self._connected or self._w3 is None:
            return None
        if getattr(self, "_medical_contract", None):
            return self._medical_contract

        contract_addr = env_str("MEDICAL_CONTRACT_ADDRESS", "").strip()
        contract = None
        if contract_addr:
            contract = self.load_contract("MedicalDataManager", contract_addr)

        if contract is None:
            addr_from_file = self._load_deployed_address("MedicalDataManager")
            if addr_from_file:
                contract = self.load_contract("MedicalDataManager", addr_from_file)

        if contract is None:
            deployed = self.deploy("MedicalDataManager")
            if deployed:
                _, contract = deployed

        if contract is not None:
            self._medical_contract = contract
        return contract

    def _normalize_hash(self, data_hash: str) -> str:
        digest = data_hash[2:] if data_hash.startswith("0x") else data_hash
        if len(digest) != 64:
            raise ValueError("data_hash must be a 32-byte hex string")
        return digest.lower()

    def _hash_to_bytes(self, data_hash: str) -> bytes:
        digest = self._normalize_hash(data_hash)
        return bytes.fromhex(digest)

    def _to_transaction_dict(self, receipt) -> Dict[str, Any]:
        tx_hash = None
        block_number = None
        status = None
        if receipt is None:
            return {}
        try:
            tx_hash = receipt["transactionHash"]
        except Exception:
            tx_hash = getattr(receipt, "transactionHash", None)
        if hasattr(tx_hash, "hex"):
            tx_hash = tx_hash.hex()
        try:
            block_number = receipt.get("blockNumber")
        except Exception:
            block_number = getattr(receipt, "blockNumber", None)
        try:
            status = receipt.get("status")
        except Exception:
            status = getattr(receipt, "status", None)
        return {"transactionHash": tx_hash, "blockNumber": block_number, "status": status}

    def _record_local_pointer(
        self,
        patient_id: str,
        ipfs_cid: str,
        data_hash: str,
        tx_hash: Optional[str],
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not hasattr(self, "_record_cache"):
            self._record_cache: Dict[str, Dict[str, Any]] = {}
        if not hasattr(self, "_tx_counter"):
            self._tx_counter = 0
        timestamp = timestamp or int(time.time())
        if tx_hash is None:
            self._tx_counter += 1
            tx_hash = f"0x{self._tx_counter:064x}"
        record = {
            "patient_id": patient_id,
            "ipfs_cid": ipfs_cid,
            "cid": ipfs_cid,
            "data_hash": self._normalize_hash(data_hash),
            "timestamp": timestamp,
            "tx_hash": tx_hash,
        }
        self._record_cache[patient_id] = record
        return record

    def store_medical_data_pointer(self, patient_id: str, ipfs_cid: str, data_hash: str):
        timestamp = int(time.time())
        if not self.is_enabled() or not self._ensure_connection():
            record = self._record_local_pointer(patient_id, ipfs_cid, data_hash, tx_hash=None, timestamp=timestamp)
            return {"transactionHash": record["tx_hash"], "status": "SIMULATED"}

        contract = self._get_medical_manager()
        if contract is None:
            record = self._record_local_pointer(patient_id, ipfs_cid, data_hash, tx_hash=None, timestamp=timestamp)
            return {"transactionHash": record["tx_hash"], "status": "SIMULATED"}

        try:
            hashed_bytes = self._hash_to_bytes(data_hash)
        except ValueError:
            # Fallback to simulated storage for malformed hash
            record = self._record_local_pointer(patient_id, ipfs_cid, data_hash, tx_hash=None, timestamp=timestamp)
            return {"transactionHash": record["tx_hash"], "status": "SIMULATED"}

        receipt = self._build_and_send(
            contract.functions.storeMedicalData(patient_id, ipfs_cid, hashed_bytes),
            return_receipt=True,
        )
        tx_info = self._to_transaction_dict(receipt)
        tx_hash = tx_info.get("transactionHash")
        self._record_local_pointer(patient_id, ipfs_cid, data_hash, tx_hash=tx_hash, timestamp=timestamp)
        return tx_info

    def register_medical_record(self, patient_id: str, ipfs_cid: str, data_hash: str) -> Optional[str]:
        tx_info = self.store_medical_data_pointer(patient_id, ipfs_cid, data_hash)
        if isinstance(tx_info, dict):
            return tx_info.get("transactionHash")
        return tx_info

    def update_medical_record_pointer(self, patient_id: str, new_ipfs_cid: str, new_data_hash: str) -> Optional[str]:
        return self.register_medical_record(patient_id, new_ipfs_cid, new_data_hash)

    def get_medical_record_cid(self, patient_id: str) -> Optional[str]:
        if hasattr(self, "_record_cache") and patient_id in self._record_cache:
            return self._record_cache[patient_id]["cid"]

        if not self.is_enabled() or not self._ensure_connection():
            return None

        contract = self._get_medical_manager()
        if contract is None:
            return None
        try:
            record = contract.functions.medicalRecords(patient_id).call()
            if not record:
                return None
            ipfs_hash = record[0]
            return ipfs_hash
        except Exception:
            return None

    def get_medical_record(self, patient_id: str) -> Optional[Dict[str, Any]]:
        if hasattr(self, "_record_cache") and patient_id in self._record_cache:
            return self._record_cache[patient_id]

        if not self.is_enabled() or not self._ensure_connection():
            return None

        contract = self._get_medical_manager()
        if contract is None:
            return None
        try:
            record = contract.functions.medicalRecords(patient_id).call()
        except Exception:
            return None
        if not record:
            return None
        ipfs_hash = record[0]
        ciphertext = record[1]
        last_updated = record[2]
        data_hash = None
        if hasattr(ciphertext, "hex"):
            data_hash = ciphertext.hex()
        elif isinstance(ciphertext, (bytes, bytearray)):
            data_hash = ciphertext.hex()
        else:
            data_hash = str(ciphertext)

        tx_hash = None
        if hasattr(self, "_record_cache") and patient_id in self._record_cache:
            tx_hash = self._record_cache[patient_id].get("tx_hash")

        record_dict = {
            "patient_id": patient_id,
            "ipfs_cid": ipfs_hash,
            "cid": ipfs_hash,
            "data_hash": self._normalize_hash(data_hash) if data_hash else None,
            "timestamp": int(last_updated) if last_updated else 0,
            "tx_hash": tx_hash,
        }
        self._record_local_pointer(patient_id, ipfs_hash, record_dict["data_hash"] or "0" * 64, tx_hash=tx_hash, timestamp=int(last_updated) if last_updated else None)
        return record_dict


def get_evm_client() -> Optional[EVMClient]:
    client = EVMClient()
    if not client.is_enabled():
        return None
    if not client.connect():
        return None
    return client
