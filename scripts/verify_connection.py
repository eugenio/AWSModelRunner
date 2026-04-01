"""Verify NadirClaw proxy is running and Bedrock models are reachable."""

import json
import sys
import urllib.request
import urllib.error

PROXY_URL = "http://127.0.0.1:4000"
MODELS_TO_TEST = [
    ("eco", "Say hello in one word."),
    ("auto", "Write a Python function to reverse a string."),
    (
        "premium",
        "Explain the difference between a mutex and a semaphore in one sentence.",
    ),
]


def check_health():
    try:
        req = urllib.request.Request(f"{PROXY_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"Health check: {resp.status} OK")
            return True
    except urllib.error.URLError as e:
        print(f"Health check FAILED: {e}")
        print("Is NadirClaw running? Start with: pixi run start")
        return False


def test_model(profile: str, prompt: str):
    payload = json.dumps(
        {
            "model": profile,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
        }
    ).encode()

    req = urllib.request.Request(
        f"{PROXY_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            model_used = data.get("model", "unknown")
            content = data["choices"][0]["message"]["content"][:80]
            print(f"  [{profile}] -> {model_used}: {content}...")
            return True
    except urllib.error.URLError as e:
        print(f"  [{profile}] FAILED: {e}")
        return False


def main():
    print("=== NadirClaw + Bedrock Connection Verify ===\n")

    if not check_health():
        sys.exit(1)

    print("\nTesting model routing:")
    all_ok = True
    for profile, prompt in MODELS_TO_TEST:
        if not test_model(profile, prompt):
            all_ok = False

    print()
    if all_ok:
        print("All models reachable. Setup is working.")
    else:
        print("Some models failed. Check AWS Bedrock model access in eu-west-1.")
        sys.exit(1)


if __name__ == "__main__":
    main()
