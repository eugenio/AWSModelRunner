"""Manage NadirClaw secrets via Windows Credential Manager (keyring).

Stores and retrieves the Bedrock Mantle API key securely.
Docker needs an env file at runtime, so this script generates it
on-the-fly from the keyring.

Usage:
    python scripts/manage_keys.py set --mantle KEY
    python scripts/manage_keys.py get
    python scripts/manage_keys.py gen-env
    python scripts/manage_keys.py clean-env
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import keyring

SERVICE = "nadirclaw"
NADIRCLAW_DIR = Path.home() / ".nadirclaw"


def cmd_set(args: argparse.Namespace) -> None:
    """Store Bedrock Mantle API key in Windows Credential Manager."""
    if args.mantle:
        keyring.set_password(SERVICE, "mantle_api_key", args.mantle)
        print("  Stored mantle_api_key")
    else:
        print("No key provided. Usage:")
        print("  python scripts/manage_keys.py set --mantle YOUR_KEY")


def cmd_get(args: argparse.Namespace) -> None:
    """Show current key (masked)."""
    value = keyring.get_password(SERVICE, "mantle_api_key")
    if value:
        masked = value[:8] + "..." + value[-4:]
        print(f"  mantle_api_key: {masked}")
    else:
        print("  mantle_api_key: NOT SET")


def cmd_gen_env(args: argparse.Namespace) -> None:
    """Generate mantle.env for docker-compose from keyring."""
    NADIRCLAW_DIR.mkdir(exist_ok=True)

    mantle_key = keyring.get_password(SERVICE, "mantle_api_key")
    if not mantle_key:
        print("ERROR: mantle_api_key not found in keyring.")
        print("  Run: python scripts/manage_keys.py set --mantle YOUR_KEY")
        sys.exit(1)

    mantle_env = NADIRCLAW_DIR / "mantle.env"
    mantle_env.write_text(f"OPENAI_API_KEY={mantle_key}\n", encoding="utf-8")
    print(f"  Generated {mantle_env}")


def cmd_clean_env(args: argparse.Namespace) -> None:
    """Remove generated .env files (key stays in keyring)."""
    path = NADIRCLAW_DIR / "mantle.env"
    if path.exists():
        path.unlink()
        print(f"  Removed {path}")


def main() -> None:
    """Entry point for the secrets manager CLI."""
    parser = argparse.ArgumentParser(description="NadirClaw secrets manager (Windows keyring)")
    sub = parser.add_subparsers(dest="command", required=True)
    p_set = sub.add_parser("set", help="Store Bedrock Mantle API key")
    p_set.add_argument("--mantle", help="Bedrock Mantle API key (OPENAI_API_KEY)")
    sub.add_parser("get", help="Show current key (masked)")
    sub.add_parser("gen-env", help="Generate mantle.env for Docker from keyring")
    sub.add_parser("clean-env", help="Remove generated .env files")

    args = parser.parse_args()
    dispatch = {"set": cmd_set, "get": cmd_get, "gen-env": cmd_gen_env, "clean-env": cmd_clean_env}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
