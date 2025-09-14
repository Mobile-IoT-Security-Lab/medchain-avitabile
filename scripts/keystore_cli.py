#!/usr/bin/env python3
"""Keystore CLI for dataset encryption keys.

Supports:
- FileKeyProvider (scrypt + AES-GCM wrapped keys on disk)
- EnvKeyProvider (env vars)

Commands:
  list      Show known key ids and active key
  rotate    Create or set a new active key (optionally from provided base64)

Examples:
  # File provider: create/rotate keystore and list keys
  scripts/keystore_cli.py rotate --provider file --keystore keystore.json --passphrase 'change-me'
  scripts/keystore_cli.py list   --provider file --keystore keystore.json --passphrase 'change-me'

  # Env provider: rotate and print export commands
  scripts/keystore_cli.py rotate --provider env --print-exports
  scripts/keystore_cli.py list   --provider env
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from getpass import getpass

# Ensure project root on sys.path when invoked from repo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from medical.key_provider import EnvKeyProvider, FileKeyProvider  # type: ignore


def cmd_list_env(args: argparse.Namespace) -> int:
    prov = EnvKeyProvider()
    key, kid = prov.get_active_key()
    kids = prov.list_kids()
    out = {
        "provider": "env",
        "active": kid,
        "known": kids,
        "has_key": bool(key),
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_rotate_env(args: argparse.Namespace) -> int:
    prov = EnvKeyProvider()
    new_key: bytes
    if args.new_key_base64:
        try:
            new_key = base64.b64decode(args.new_key_base64)
        except Exception:
            print("Invalid base64 for --new-key-base64", file=sys.stderr)
            return 2
        if len(new_key) not in (16, 24, 32):
            print("Key must be 16/24/32 bytes", file=sys.stderr)
            return 2
    else:
        new_key = os.urandom(32)
    key, kid = prov.rotate(new_key=new_key)
    if not key:
        print("Rotation failed", file=sys.stderr)
        return 1
    exports = {
        "IPFS_ENC_KEY": base64.b64encode(key).decode(),
        "IPFS_ENC_KEY_ID": kid,
        "IPFS_ENC_KEYS": os.getenv("IPFS_ENC_KEYS", "{}"),
    }
    print(json.dumps({"provider": "env", "rotated": True, "kid": kid}, indent=2))
    if args.print_exports:
        print("\n# Export these in your shell:", file=sys.stdout)
        for k, v in exports.items():
            print(f"export {k}='{v}'")
    return 0


def _ensure_passphrase(args: argparse.Namespace) -> str:
    if args.passphrase:
        return args.passphrase
    env = os.getenv("IPFS_KEYSTORE_PASSPHRASE")
    if env:
        return env
    return getpass("Keystore passphrase: ")


def cmd_list_file(args: argparse.Namespace) -> int:
    pw = _ensure_passphrase(args)
    prov = FileKeyProvider(args.keystore, passphrase=pw)
    key, kid = prov.get_active_key()
    kids = prov.list_kids()
    out = {
        "provider": "file",
        "keystore": args.keystore,
        "active": kid,
        "known": kids,
        "has_key": bool(key),
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_rotate_file(args: argparse.Namespace) -> int:
    pw = _ensure_passphrase(args)
    prov = FileKeyProvider(args.keystore, passphrase=pw)
    new_key: bytes | None = None
    if args.new_key_base64:
        try:
            new_key = base64.b64decode(args.new_key_base64)
        except Exception:
            print("Invalid base64 for --new-key-base64", file=sys.stderr)
            return 2
        if len(new_key) not in (16, 24, 32):
            print("Key must be 16/24/32 bytes", file=sys.stderr)
            return 2
    key, kid = prov.rotate(new_key=new_key)
    if not key:
        print("Rotation failed", file=sys.stderr)
        return 1
    print(json.dumps({"provider": "file", "keystore": args.keystore, "rotated": True, "kid": kid}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Keystore CLI for dataset encryption keys")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--provider", choices=["file", "env"], required=True, help="Key provider type")

    ap_list = sub.add_parser("list", parents=[common], help="List known keys and active key")
    ap_list.add_argument("--keystore", help="Path to keystore (file provider)")
    ap_list.add_argument("--passphrase", help="Passphrase for keystore (file provider)")

    ap_rot = sub.add_parser("rotate", parents=[common], help="Rotate to a new key")
    ap_rot.add_argument("--keystore", help="Path to keystore (file provider)")
    ap_rot.add_argument("--passphrase", help="Passphrase for keystore (file provider)")
    ap_rot.add_argument("--new-key-base64", help="Provide a specific base64 key (16/24/32 bytes)")
    ap_rot.add_argument("--print-exports", action="store_true", help="Print export lines (env provider)")

    args = ap.parse_args()
    if args.provider == "env":
        if args.cmd == "list":
            return cmd_list_env(args)
        elif args.cmd == "rotate":
            return cmd_rotate_env(args)
    elif args.provider == "file":
        if not args.keystore:
            print("--keystore is required for file provider", file=sys.stderr)
            return 2
        if args.cmd == "list":
            return cmd_list_file(args)
        elif args.cmd == "rotate":
            return cmd_rotate_file(args)
    print("Unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

