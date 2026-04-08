"""Setup script: copies NadirClaw config and verifies AWS credentials."""

import shutil
import subprocess
import sys
from pathlib import Path

NADIRCLAW_DIR = Path.home() / ".nadirclaw"
CONFIG_SOURCE = Path(__file__).parent.parent / "config" / "nadirclaw.env"


def main():
    # 1. Create NadirClaw config directory
    NADIRCLAW_DIR.mkdir(exist_ok=True)
    target = NADIRCLAW_DIR / ".env"

    if target.exists():
        print(f"Config already exists at {target}")
        resp = input("Overwrite? [y/N] ").strip().lower()
        if resp != "y":
            print("Skipping config copy.")
        else:
            shutil.copy2(CONFIG_SOURCE, target)
            print(f"Config copied to {target}")
    else:
        shutil.copy2(CONFIG_SOURCE, target)
        print(f"Config copied to {target}")

    # 2. Verify AWS credentials
    print("\nVerifying AWS credentials...")
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--region", "eu-west-2"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"AWS credentials OK: {result.stdout.strip()}")
    else:
        print(f"AWS credentials FAILED: {result.stderr.strip()}")
        print("Configure with: aws configure --profile default")
        sys.exit(1)

    # 3. Remind about Bedrock model access
    print(
        "\nReminder: Request access to these models in the AWS Bedrock console (eu-west-2):"
    )
    print("  - Qwen3 Coder 30B (qwen.qwen3-coder-30b-a3b-v1:0)")
    print("  - Qwen3 Coder 480B (qwen.qwen3-coder-480b-a35b-v1:0)")
    print("  - Kimi K2.5 (moonshotai.kimi-k2.5)")
    print("\nSetup complete. Run: pixi run -e dev up")


if __name__ == "__main__":
    main()
