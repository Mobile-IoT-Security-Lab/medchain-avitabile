"""KeyProvider interface and implementations for dataset encryption keys.

Supports:
- EnvKeyProvider: reads base64 key from environment variables.
- FileKeyProvider: stores AES key encrypted (scrypt + AES-GCM) with a passphrase.
"""
from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import os
import base64
import json
import hashlib

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt  # type: ignore
except Exception:  # pragma: no cover
    AESGCM = None  # type: ignore
    Scrypt = None  # type: ignore


def _compute_kid(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:16]


class KeyProvider:
    """Abstract base provider for encryption keys."""

    def get_active_key(self) -> Tuple[Optional[bytes], Optional[str]]:
        """Return (key_bytes, key_id) for the active key, or (None, None)."""
        raise NotImplementedError

    def rotate(self, new_key: Optional[bytes] = None, **kwargs) -> Tuple[Optional[bytes], Optional[str]]:
        """Rotate to a new key (optionally provided). Returns (key_bytes, key_id)."""
        raise NotImplementedError

    def resolve_key(self, kid: str) -> Optional[bytes]:
        """Return key material for a specific key id, if available."""
        return None

    def list_kids(self) -> list[str]:
        """Return known key ids, if applicable."""
        return []


class EnvKeyProvider(KeyProvider):
    """Reads base64 key from environment variables.

    Env vars:
      - IPFS_ENC_KEY: base64-encoded 16/24/32-byte AES key
      - IPFS_ENC_KEY_ID (optional): key id label. If missing, computed from key (sha256 truncated).
    """

    def __init__(self, key_var: str = "IPFS_ENC_KEY", id_var: str = "IPFS_ENC_KEY_ID", pool_var: str = "IPFS_ENC_KEYS"):
        self.key_var = key_var
        self.id_var = id_var
        self.pool_var = pool_var  # JSON mapping kid -> base64 key

    def get_active_key(self) -> Tuple[Optional[bytes], Optional[str]]:
        b64 = os.getenv(self.key_var)
        if not b64:
            return None, None
        try:
            key = base64.b64decode(b64)
        except Exception:
            return None, None
        if len(key) not in (16, 24, 32):
            return None, None
        kid = os.getenv(self.id_var) or _compute_kid(key)
        return key, kid

    def rotate(self, new_key: Optional[bytes] = None, **kwargs) -> Tuple[Optional[bytes], Optional[str]]:
        key = new_key or os.urandom(32)
        os.environ[self.key_var] = base64.b64encode(key).decode()
        kid = _compute_kid(key)
        os.environ[self.id_var] = kid
        # Update pool mapping
        pool = {}
        raw = os.getenv(self.pool_var)
        if raw:
            try:
                pool = json.loads(raw)
            except Exception:
                pool = {}
        pool[kid] = base64.b64encode(key).decode()
        os.environ[self.pool_var] = json.dumps(pool)
        return key, kid

    def resolve_key(self, kid: str) -> Optional[bytes]:
        # Check active first
        k, active_kid = self.get_active_key()
        if k is not None and active_kid == kid:
            return k
        # Then check pool
        raw = os.getenv(self.pool_var)
        if not raw:
            return None
        try:
            pool = json.loads(raw)
        except Exception:
            return None
        b64 = pool.get(kid)
        if not b64:
            return None
        try:
            key = base64.b64decode(b64)
        except Exception:
            return None
        if len(key) not in (16, 24, 32):
            return None
        return key

    def list_kids(self) -> list[str]:
        kids: list[str] = []
        _, active_kid = self.get_active_key()
        if active_kid:
            kids.append(active_kid)
        raw = os.getenv(self.pool_var)
        if raw:
            try:
                pool = json.loads(raw)
                kids.extend([k for k in pool.keys() if k not in kids])
            except Exception:
                pass
        return kids


class FileKeyProvider(KeyProvider):
    """Stores AES key encrypted with passphrase using scrypt + AES-GCM.

    File format (JSON): { v, wrap, params:{n,r,p}, salt, nonce, ciphertext, klen, kid }
    """

    def __init__(self, path: str, passphrase: Optional[str] = None):
        self.path = path
        self.passphrase = passphrase or os.getenv("IPFS_KEYSTORE_PASSPHRASE") or ""
        self._params = {"n": 2 ** 14, "r": 8, "p": 1}

    def _kdf(self, salt: bytes) -> Optional[bytes]:
        if Scrypt is None:
            return None
        kdf = Scrypt(salt=salt, length=32, n=self._params["n"], r=self._params["r"], p=self._params["p"])  # type: ignore
        return kdf.derive(self.passphrase.encode())

    def _wrap_single(self, key: bytes) -> Optional[Dict[str, Any]]:
        if AESGCM is None:
            return None
        salt = os.urandom(16)
        aes_key = self._kdf(salt)
        if aes_key is None:
            return None
        nonce = os.urandom(12)
        aes = AESGCM(aes_key)
        ct = aes.encrypt(nonce, key, None)
        entry = {
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ct).decode(),
            "klen": len(key),
            "kid": _compute_kid(key),
        }
        return entry

    def _unwrap_single(self, env: Dict[str, Any]) -> Optional[Tuple[bytes, str]]:
        if AESGCM is None:
            return None
        try:
            salt = base64.b64decode(env.get("salt", ""))
            nonce = base64.b64decode(env.get("nonce", ""))
            ct = base64.b64decode(env.get("ciphertext", ""))
            aes_key = self._kdf(salt)
            if aes_key is None:
                return None
            aes = AESGCM(aes_key)
            key = aes.decrypt(nonce, ct, None)
            kid = env.get("kid") or _compute_kid(key)
            return key, kid
        except Exception:
            return None

    def _load_keystore(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r") as f:
                env = json.load(f)
            return env
        except Exception:
            return None

    def get_active_key(self) -> Tuple[Optional[bytes], Optional[str]]:
        env = self._load_keystore()
        if env is None:
            return None, None
        # Multi-key format
        if isinstance(env, dict) and "keys" in env:
            active = env.get("active")
            for entry in env.get("keys", []):
                if entry.get("kid") == active:
                    res = self._unwrap_single(entry)
                    if res:
                        return res
            return None, None
        # Single-key legacy format
        self._params = env.get("params", self._params)
        res = self._unwrap_single(env)
        if res:
            return res
        return None, None

    def rotate(self, new_key: Optional[bytes] = None, **kwargs) -> Tuple[Optional[bytes], Optional[str]]:
        key = new_key or os.urandom(32)
        entry = self._wrap_single(key)
        if entry is None:
            return None, None
        # Load existing keystore
        env = self._load_keystore()
        if env and "keys" in env:
            keys = env.get("keys", [])
            keys.append(entry)
            env["keys"] = keys
            env["active"] = entry["kid"]
        elif env:  # upgrade legacy single-key to multi-key
            prev_params = env.get("params", self._params)
            prev_entry = {k: env[k] for k in ("salt", "nonce", "ciphertext", "klen", "kid") if k in env}
            env = {
                "v": env.get("v", 1),
                "wrap": env.get("wrap", "AES-GCM-SCRYPT"),
                "params": prev_params,
                "keys": [prev_entry, entry],
                "active": entry["kid"],
            }
        else:
            env = {
                "v": 1,
                "wrap": "AES-GCM-SCRYPT",
                "params": self._params,
                "keys": [entry],
                "active": entry["kid"],
            }
        with open(self.path, "w") as f:
            json.dump(env, f)
        return key, entry["kid"]

    def resolve_key(self, kid: str) -> Optional[bytes]:
        env = self._load_keystore()
        if not env:
            return None
        # Multi-key
        if "keys" in env:
            for entry in env.get("keys", []):
                if entry.get("kid") == kid:
                    res = self._unwrap_single(entry)
                    return res[0] if res else None
            return None
        # Single-key
        res = self._unwrap_single(env)
        if res and (env.get("kid") == kid or kid == _compute_kid(res[0])):
            return res[0]
        return None

    def list_kids(self) -> list[str]:
        env = self._load_keystore()
        if not env:
            return []
        if "keys" in env:
            return [e.get("kid", "") for e in env.get("keys", []) if e.get("kid")]
        kid = env.get("kid")
        return [kid] if kid else []
