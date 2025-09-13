"""IPFS adapter providing a real client behind a stable interface.

Usage:
    from adapters.ipfs import get_ipfs_client
    client = get_ipfs_client() or FakeIPFSClient()

Env flags:
    USE_REAL_IPFS=1                Enable real IPFS client if possible
    IPFS_API_ADDR=...              Multiaddr or HTTP address (default /ip4/127.0.0.1/tcp/5001/http)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from .config import env_bool, env_str


try:
    import ipfshttpclient  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ipfshttpclient = None  # type: ignore


class RealIPFSClient:
    """Thin wrapper around ipfshttpclient with FakeIPFSClient-like methods."""

    def __init__(self, api_addr: Optional[str] = None):
        if ipfshttpclient is None:
            raise RuntimeError("ipfshttpclient not installed; cannot create RealIPFSClient")

        addr = api_addr or env_str("IPFS_API_ADDR", "/ip4/127.0.0.1/tcp/5001/http")
        # ipfshttpclient.connect accepts multiaddr or URL
        self._client = ipfshttpclient.connect(addr)  # may raise if daemon not running

    # Compatibility helpers
    def add(self, content: str, pin: bool = True) -> str:
        # Add as bytes; returns CID string
        cid = self._client.add_bytes(content.encode())
        if pin:
            try:
                self._client.pin.add(cid)
            except Exception:
                pass
        return cid

    def get(self, ipfs_hash: str) -> Optional[str]:
        try:
            data: bytes = self._client.cat(ipfs_hash)
            return data.decode(errors="replace")
        except Exception:
            return None

    def pin(self, ipfs_hash: str) -> bool:
        try:
            self._client.pin.add(ipfs_hash)
            return True
        except Exception:
            return False

    def unpin(self, ipfs_hash: str) -> bool:
        try:
            self._client.pin.rm(ipfs_hash)
            return True
        except Exception:
            return False

    def rm(self, ipfs_hash: str) -> bool:
        """Simulate deletion by unpinning; IPFS content is immutable.
        Garbage collection is node-controlled and may require `repo.gc()`.
        """
        ok = self.unpin(ipfs_hash)
        # Best effort: do not call repo.gc() automatically
        return ok

    def ls(self) -> List[str]:
        try:
            pins = self._client.pin.ls(type="all") or {}
            keys = list((pins.get("Keys") or pins).keys())  # schema differs by version
            return keys
        except Exception:
            return []

    def stat(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        # Try object.stat first, then block/stat fallbacks
        try:
            st = self._client.object.stat(ipfs_hash)
            size = st.get("CumulativeSize") or st.get("DataSize") or 0
            return {"hash": ipfs_hash, "size": int(size), "pinned": ipfs_hash in set(self.ls()), "type": "object"}
        except Exception:
            try:
                st2 = self._client.block.stat(ipfs_hash)
                size2 = st2.get("Size", 0)
                return {"hash": ipfs_hash, "size": int(size2), "pinned": ipfs_hash in set(self.ls()), "type": "block"}
            except Exception:
                return None


def get_ipfs_client() -> Optional[RealIPFSClient]:
    """Return a RealIPFSClient if env allows and ipfshttpclient is available and reachable.

    Otherwise, return None so callers can fall back to the simulated client.
    """
    if not env_bool("USE_REAL_IPFS", False):
        return None
    try:
        return RealIPFSClient()
    except Exception:
        return None

