"""Simple env-driven config helpers for backend adapters.

I keep dependencies optional and avoid importing heavy libs unless flags are set.
If python-dotenv is available, load it, but do not require it.
"""
from __future__ import annotations

import os
from typing import Optional


# Load .env if python-dotenv is available (optional)
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()  # best-effort; ignored if no .env present
except Exception:
    pass


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    val = val.strip().lower()
    return val in {"1", "true", "yes", "on"}


def env_str(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    return val
