"""Manage NadirClaw secrets via Windows Credential Manager (keyring).

Stores and retrieves API keys securely instead of plain-text .env files.
Docker needs env files at runtime, so this script generates them on-the-fly
from the keyring and cleans up after docker-compose starts.

Usage:
    python scripts/secrets.py set --mantle KEY --openrouter KEY
    python scripts/secrets.py set --mantle KEY     # set only mantle
    python scripts/secrets.py get                  # print current keys (masked)
    python scripts/secrets.py gen-env              # generate .env files for Docker
    python scripts/secrets.py clean-env            # remove generated .env files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import keyring

SERVICE = "nadirclaw"
KEYS = {
    "mantle_api_key": "Bedrock Mantle API key (OPENAI_API_KEY)",
    "openrouter_api_key": "OpenRouter API key (OPENROUTER_API_KEY)",
}

NADIRCLAW_DIR = Path.home() / ".nadirclaw"


def cmd_set(args: argparse.Namespace) -> None:
    """Store API keys in Windows Credential Manager."""
    arg_map = {"mantle_api_key": args.mantle, "openrouter_api_key": args.openrouter}
    any_set = False
    for key_name, value in arg_map.items():
        if value:
            keyring.set_password(SERVICE, key_name, value)
            print(f"  Stored {key_name}")
            any_set = True
    if not any_set:
        print("No keys provided. Usage:")
        print("  python scripts/secrets.py set --mantle YOUR_KEY --openrouter YOUR_KEY")


def cmd_get(args: argparse.Namespace) -> None:
    """Show current keys (masked)."""
    for key_name, description in KEYS.items():
        value = keyring.get_password(SERVICE, key_name)
        if value:
            masked = value[:8] + "..." + value[-4:]
            print(f"  {key_name}: {masked}")
        else:
            print(f"  {key_name}: NOT SET")


def cmd_gen_env(args: argparse.Namespace) -> None:
    """Generate .env files for docker-compose from keyring secrets."""
    NADIRCLAW_DIR.mkdir(exist_ok=True)

    mantle_key = keyring.get_password(SERVICE, "mantle_api_key")
    openrouter_key = keyring.get_password(SERVICE, "openrouter_api_key")

    if not mantle_key:
        print("ERROR: mantle_api_key not found in keyring. Run: python scripts/secrets.py set")
        sys.exit(1)

    mantle_env = NADIRCLAW_DIR / "mantle.env"
    mantle_env.write_text(f"OPENAI_API_KEY={mantle_key}\n", encoding="utf-8")
    print(f"  Generated {mantle_env}")

    openrouter_env = NADIRCLAW_DIR / "openrouter.env"
    if openrouter_key:
        openrouter_env.write_text(f"OPENROUTER_API_KEY={openrouter_key}\n", encoding="utf-8")
        print(f"  Generated {openrouter_env}")
    else:
        openrouter_env.write_text("OPENROUTER_API_KEY=\n", encoding="utf-8")
        print(f"  Generated {openrouter_env} (empty — OpenRouter will fail)")


def cmd_clean_env(args: argparse.Namespace) -> None:
    """Remove generated .env files (secrets stay in keyring)."""
    for name in ("mantle.env", "openrouter.env"):
        path = NADIRCLAW_DIR / name
        if path.exists():
            path.unlink()
            print(f"  Removed {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NadirClaw secrets manager (Windows keyring)")
    sub = parser.add_subparsers(dest="command", required=True)
    p_set = sub.add_parser("set", help="Store API keys in Windows Credential Manager")
    p_set.add_argument("--mantle", help="Bedrock Mantle API key (OPENAI_API_KEY)")
    p_set.add_argument("--openrouter", help="OpenRouter API key (OPENROUTER_API_KEY)")
    sub.add_parser("get", help="Show current keys (masked)")
    sub.add_parser("gen-env", help="Generate .env files for Docker from keyring")
    sub.add_parser("clean-env", help="Remove generated .env files")

    args = parser.parse_args()
    dispatch = {"set": cmd_set, "get": cmd_get, "gen-env": cmd_gen_env, "clean-env": cmd_clean_env}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
