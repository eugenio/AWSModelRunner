# AWS Model Runner — Setup Guide

**Build a self-hosted, cost-optimized AI coding assistant with automatic model routing.**

This guide walks you through setting up a 3-tier coding model router on AWS Bedrock with NadirClaw, Tailscale VPN, and OpenCode. Total cost: ~30-55 EUR/mo for a solo developer (incl. VAT).

---

## Architecture Overview

```
Your Machine                          AWS (eu-west-2 London)
+------------------+                  +---------------------------+
| OpenCode (TUI)   |                  | VPC (private subnets)     |
|   model: auto    |                  |                           |
+--------+---------+                  |  +---------------------+  |
         |                            |  | VPC Endpoint         |  |
         v                            |  | (bedrock-runtime)    |  |
+------------------+   Tailscale      |  +----------+----------+  |
| NadirClaw        +--tunnel (opt)--->|             |              |
| (localhost:4000) |                  |  +----------v----------+  |
| 3-tier classifier|                  |  | Amazon Bedrock       |  |
+--+-----+-----+--+                  |  |  - Qwen3 30B (cheap) |  |
   |     |     |                      |  |  - Qwen3 480B (mid)  |  |
   v     v     v                      |  |  - Kimi K2.5 (best)  |  |
 Simple  Mid  Complex                 |  +---------------------+  |
                                      +---------------------------+
```

**How it works:** NadirClaw classifies each prompt's complexity using a local sentence-embedding model (~10ms), then routes to the cheapest model that can handle it. Simple tasks go to Qwen3 30B, complex tasks to Kimi K2.5.

---

## Prerequisites

- AWS account with billing enabled
- AWS CLI v2 installed and configured (`aws configure`)
- Python 3.11+
- Node.js 18+ (for AWS CDK)
- [pixi](https://pixi.sh) package manager (recommended) or pip
- [Tailscale](https://tailscale.com) account (free tier, optional for VPN)
- ~30 minutes

---

## Step 1: Clone and Install

```bash
git clone <this-repo-url>
cd aws-model-runner

# Install dependencies
pixi install

# Or without pixi:
pip install nadirclaw[dashboard] boto3
```

---

## Step 2: Request Bedrock Model Access

1. Go to the [AWS Bedrock Console](https://eu-west-2.console.aws.amazon.com/bedrock/home?region=eu-west-2#/modelaccess)
2. Select region: **eu-west-2 (London)**
3. Click **Manage model access**
4. Request access for:
   - **Qwen3-Coder-30B-A3B-Instruct** (Qwen)
   - **Qwen3 Coder 480B A35B Instruct** (Qwen)
   - **Kimi K2.5** (Moonshot AI)
5. Wait for approval (usually instant for these models)

**Verify access:**

```bash
aws bedrock list-foundation-models --region eu-west-2 \
  --query "modelSummaries[?contains(modelId,'qwen3-coder') || contains(modelId,'kimi')].{id:modelId,status:modelLifecycle.status}" \
  --output table
```

---

## Step 3: Deploy AWS Infrastructure (CDK)

This creates: VPC with private subnets, VPC Endpoint for Bedrock (private connectivity), IAM role with least-privilege access, CloudWatch (prompt logging disabled).

```bash
# Install CDK CLI
npm install -g aws-cdk

# Bootstrap CDK in eu-west-2 (one-time)
cd infra
pip install -r requirements.txt   # or: python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt
cdk bootstrap aws://YOUR_ACCOUNT_ID/eu-west-2

# Deploy network + Bedrock stacks
cdk deploy ModelRunnerNetwork ModelRunnerBedrock --require-approval never
```

**Expected output:**

```
Outputs:
ModelRunnerNetwork.VpcId = vpc-0xxxxxxxxx
ModelRunnerBedrock.BedrockEndpointId = vpce-0xxxxxxxxx
ModelRunnerBedrock.InvokeRoleArn = arn:aws:iam::ACCOUNT:role/model-runner-bedrock-invoke-eu-west-2
```

**Cost:** ~9.28 EUR/mo (VPC endpoint) + ~10.49 EUR/mo (NAT gateway) = ~20 EUR/mo infra

### Optional: Deploy Tailscale Subnet Router

This adds a secure VPN tunnel so Bedrock traffic never touches the public internet.

1. Get an auth key from https://login.tailscale.com/admin/settings/keys (reusable, tag: `model-runner`)
2. Deploy:

```bash
cdk deploy ModelRunnerTailscale -c tailscale_auth_key=tskey-auth-YOUR_KEY
```

3. Approve subnet routes in [Tailscale Admin](https://login.tailscale.com/admin/machines)

**Cost:** ~10.49 EUR/mo (t3.micro) + free Tailscale personal plan

---

## Step 4: Configure NadirClaw

```bash
# Copy the pre-built config
mkdir -p ~/.nadirclaw
cp config/nadirclaw.env ~/.nadirclaw/.env

# Or run the interactive setup
pixi run nadirclaw setup
```

**Key settings in `~/.nadirclaw/.env`:**

```bash
# AWS region
AWS_DEFAULT_REGION=eu-west-2

# 3-tier model routing
NADIRCLAW_SIMPLE_MODEL=bedrock/qwen.qwen3-coder-30b-a3b-v1:0
NADIRCLAW_MID_MODEL=bedrock/qwen.qwen3-coder-480b-a35b-v1:0
NADIRCLAW_COMPLEX_MODEL=bedrock/moonshotai.kimi-k2.5

# Thresholds (tune these based on your experience)
NADIRCLAW_TIER_THRESHOLDS=0.35,0.65

# Budget limits
NADIRCLAW_DAILY_BUDGET=5.00
NADIRCLAW_MONTHLY_BUDGET=80.00

# Server
NADIRCLAW_PORT=4000
```

---

## Step 5: Start and Verify

```bash
# Start NadirClaw
pixi run start
# Or: nadirclaw serve

# In another terminal, verify health
curl http://127.0.0.1:4000/health

# Test routing
pixi run verify
# Or: python scripts/verify_connection.py
```

**Expected behavior:**

| Prompt | Expected Tier | Model |
|---|---|---|
| "Say hello" | Simple | Qwen3 Coder 30B |
| "Write a binary search function" | Simple/Mid | Qwen3 30B or 480B |
| "Analyze race conditions in concurrent hash map with CAS" | Complex | Kimi K2.5 |

---

## Step 6: Connect OpenCode

The `opencode.json` in the project root is pre-configured. Just start OpenCode:

```bash
# Install OpenCode if needed
npm install -g opencode

# Start in project directory (picks up opencode.json automatically)
opencode
```

Or configure manually in OpenCode settings:

```
Provider: OpenAI-compatible
Base URL: http://127.0.0.1:4000/v1
API Key:  local
Model:    auto
```

**Model profiles available:**

| Profile | Routes to | Use when |
|---|---|---|
| `auto` | Classifier decides | Default — let NadirClaw pick |
| `eco` | Budget (Qwen3 30B) | Force cheap model |
| `premium` | Premium (Kimi K2.5) | Force best model |

---

## Step 7: Monitor and Tune

```bash
# Live dashboard
pixi run dashboard
# Or: nadirclaw dashboard

# Cost report
pixi run report
# Or: nadirclaw report --by-model

# Savings vs all-premium
pixi run savings
# Or: nadirclaw savings

# Export logs
nadirclaw export --format csv --since 7d
```

### Tuning Thresholds

The `NADIRCLAW_TIER_THRESHOLDS=simple_max,complex_min` controls routing:

| Setting | Effect | When to use |
|---|---|---|
| `0.35,0.65` (default) | Balanced — most go to budget | General development |
| `0.25,0.55` | More goes to mid/premium | When quality matters more |
| `0.45,0.75` | More stays on budget | When saving money matters more |
| `0.20,0.40` | Almost everything premium | Code review, security audit |

Adjust and restart NadirClaw: edit `~/.nadirclaw/.env`, then restart with `pixi run start`.

---

## Cost Summary (Solo Developer, incl. 20% VAT)

| Component | Monthly (EUR) |
|---|---|
| NadirClaw | Free (open source) |
| Bedrock inference (medium use, Mix B) | ~55 |
| VPC Endpoint | ~9 |
| NAT Gateway | ~10 |
| Tailscale (personal) | Free |
| EC2 t3.micro (Tailscale router, optional) | ~10 |
| **Total (without Tailscale)** | **~74** |
| **Total (with Tailscale)** | **~84** |

At light use: ~30-40 EUR/mo. At heavy use: ~80-120 EUR/mo.

---

## Troubleshooting

### "The provided model identifier is invalid"

The model isn't available in your region or you haven't requested access. Check:

```bash
aws bedrock list-foundation-models --region eu-west-2 \
  --query "modelSummaries[?modelId=='MODEL_ID'].modelId" --output text
```

### NadirClaw routes everything to budget

Your threshold is too high. Lower `NADIRCLAW_TIER_THRESHOLDS` (e.g., `0.25,0.55`).

### Anthropic models require use case form

Claude models on Bedrock require submitting a use case form in the AWS console before access is granted. Non-Anthropic models (Qwen, Kimi, Mistral) are usually instant.

### Port already in use

```bash
# Find and kill the process
netstat -ano | grep :4000
taskkill /F /PID <PID>    # Windows
kill <PID>                 # Linux/Mac
```

### CDK bootstrap fails

Ensure your AWS user has `AdministratorAccess` or at minimum: CloudFormation, IAM, EC2, VPC, S3, SSM, ECR permissions.

### First request is slow (~3 seconds)

Normal — NadirClaw downloads and loads the sentence-embedding model (`all-MiniLM-L6-v2`, 80 MB) on first use. Subsequent classifications take ~10ms.

---

## Cleanup

To remove all AWS resources:

```bash
cd infra

# Delete Tailscale stack (if deployed)
cdk destroy ModelRunnerTailscale -c tailscale_auth_key=dummy

# Delete Bedrock and Network stacks
cdk destroy ModelRunnerBedrock ModelRunnerNetwork

# Remove CDK bootstrap (optional)
aws cloudformation delete-stack --stack-name CDKToolkit --region eu-west-2
```

To stop NadirClaw: close the terminal or `Ctrl+C`.

---

## Alternative Models (eu-west-2)

All available in eu-west-2 London and usable as drop-in replacements in the NadirClaw config:

| Model ID | Params | Type | Notes |
|---|---|---|---|
| `qwen.qwen3-coder-30b-a3b-v1:0` | 30B MoE | Code | Budget tier (default) |
| `qwen.qwen3-coder-480b-a35b-v1:0` | 480B MoE | Code | Mid tier (default) |
| `qwen.qwen3-coder-next` | N/A | Code | New, unbenched |
| `moonshotai.kimi-k2.5` | 1T | General | Premium tier (default) |
| `deepseek.v3-v1:0` | 685B MoE | General | Strong all-rounder |
| `deepseek.v3.2` | 685B MoE | General | Latest DeepSeek |
| `zai.glm-4.7` | 355B | General | Top leaderboard |
| `zai.glm-5` | 744B | General | Top leaderboard |
| `qwen.qwen3-next-80b-a3b` | 80B MoE | General | Compact, fast |
| `nvidia.nemotron-super-3-120b` | 120B | General | NVIDIA optimized |

---

## References

- [NadirClaw](https://github.com/NadirRouter/NadirClaw) — open-source model router
- [OpenCode](https://opencode.ai/) — open-source AI coding assistant
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Onyx Open LLM Leaderboard](https://onyx.app/open-llm-leaderboard) — model benchmarks
- [Tailscale](https://tailscale.com/) — zero-config VPN
- [AWS CDK](https://docs.aws.amazon.com/cdk/) — infrastructure as code