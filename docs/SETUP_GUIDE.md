# AWS Model Runner — Setup Guide

**Build a self-hosted, cost-optimized AI coding assistant with automatic model routing.**

This guide walks you through setting up a 3-tier coding model router on AWS Bedrock with NadirClaw, Tailscale VPN, and OpenCode. Total cost: ~30-55 EUR/mo for a solo developer (incl. VAT).

---

## Architecture Overview

```
Your Machine                          AWS Bedrock (eu-west-2)
+------------------+                  +-------------------------------+
| OpenCode / Goose |                  | Bedrock Mantle endpoint       |
|   model: auto    |                  |  - Qwen3 Coder 30B  (budget) |
+--------+---------+                  |  - Qwen3 Coder 480B (mid)    |
         |                            +-------------------------------+
         v                               ^
+------------------+   Tailscale         |
| NadirClaw        +--tunnel (opt)-------+
| (localhost:4000) |
| 3-tier classifier|                  OpenRouter
+--+-----+-----+--+                  +-------------------------------+
   |     |     |                      | Qwen 3.6 Plus (premium, 1M)  |
   v     v     v                      | Free in preview               |
 Simple  Mid  Complex/Large ctx ----->+-------------------------------+
```

**How it works:** NadirClaw classifies each prompt's complexity using a local sentence-embedding model (~10ms), then routes to the cheapest model that can handle it. Simple tasks go to Qwen3 Coder 30B, complex tasks to Qwen 3.6 Plus (1M context via OpenRouter). Requests exceeding 256K context are automatically routed to Qwen 3.6 Plus regardless of complexity. Bedrock models use per-model endpoint overrides (`NADIRCLAW_MODEL_API_BASES`); OpenRouter is added as a second provider for large-context routing.

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
   - **Qwen3-Coder-30B-A3B-Instruct** (Qwen) — budget tier
   - **Qwen3 Coder 480B A35B Instruct** (Qwen) — mid tier
   - **Kimi K2.5** (Moonshot AI) — fallback
5. Wait for approval (usually instant for these models)
6. **OpenRouter (for Qwen 3.6 Plus):** Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys) — no Bedrock access needed, Qwen 3.6 Plus is free during preview

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

**Docker (recommended):** No manual config needed — the container reads `config/nadirclaw.env` automatically.

**Without Docker:**

```bash
# Copy the pre-built config
mkdir -p ~/.nadirclaw
cp config/nadirclaw.env ~/.nadirclaw/.env

# Or run the interactive setup
pixi run nadirclaw setup
```

**Key settings in `~/.nadirclaw/.env`:**

```bash
# Default Bedrock Mantle endpoint (eu-west-2)
NADIRCLAW_API_BASE=https://bedrock-mantle.eu-west-2.api.aws/v1

# OpenRouter API key (for Qwen 3.6 Plus)
OPENROUTER_API_KEY=sk-or-...

# Per-model endpoint overrides (multi-provider routing)
# Qwen 3.6 Plus routed to OpenRouter; everything else uses Bedrock
NADIRCLAW_MODEL_API_BASES=openrouter/qwen/qwen3.6-plus-preview=https://openrouter.ai/api/v1

# 3-tier model routing (Bedrock + OpenRouter)
NADIRCLAW_SIMPLE_MODEL=openai/qwen.qwen3-coder-30b-a3b-v1:0       # Bedrock, 32K ctx
NADIRCLAW_MID_MODEL=openai/qwen.qwen3-coder-480b-a35b-v1:0        # Bedrock, 256K ctx
NADIRCLAW_COMPLEX_MODEL=openrouter/qwen/qwen3.6-plus-preview       # OpenRouter, 1M ctx

# Context overflow: requests >256K tokens bypass tier classification
NADIRCLAW_CONTEXT_OVERFLOW_MODEL=openrouter/qwen/qwen3.6-plus-preview
NADIRCLAW_CONTEXT_OVERFLOW_THRESHOLD=256000

# Thresholds (tune these based on your experience)
NADIRCLAW_TIER_THRESHOLDS=0.35,0.65

# Fallback chains
NADIRCLAW_COMPLEX_FALLBACK=openai/qwen.qwen3-coder-480b-a35b-v1:0,openai/moonshotai.kimi-k2.5,openai/zai.glm-4.7

# Budget limits
NADIRCLAW_DAILY_BUDGET=5.00
NADIRCLAW_MONTHLY_BUDGET=80.00

# Server
NADIRCLAW_PORT=4000
```

> **Multi-provider routing:** `NADIRCLAW_MODEL_API_BASES` maps model name patterns to API endpoints. First match wins. Models not matching any pattern use the global `NADIRCLAW_API_BASE`. This lets you mix Bedrock Mantle with other OpenAI-compatible providers like OpenRouter. Requests exceeding `NADIRCLAW_CONTEXT_OVERFLOW_THRESHOLD` tokens are automatically routed to the overflow model (Qwen 3.6 Plus, 1M context) regardless of complexity classification.

---

## Step 5: Start and Verify

### Docker (recommended)

```bash
# Start NadirClaw (binds to 127.0.0.1:4000 only)
pixi run -e dev up

# Check logs
pixi run -e dev logs

# Verify health
curl http://127.0.0.1:4000/health

# Test routing
pixi run -e dev verify
```

> **VS Code users:** The container starts automatically when you open this project. No manual start needed.

### Without Docker

```bash
# Start NadirClaw directly (note: binds to 0.0.0.0 — use Docker for localhost-only binding)
pixi run -e dev start

# In another terminal, verify health
curl http://127.0.0.1:4000/health

# Test routing
pixi run -e dev verify
```

**Expected behavior:**

| Prompt | Expected Tier | Model |
|---|---|---|
| "Say hello" | Simple | Qwen3 Coder 30B (Bedrock) |
| "Write a binary search function" | Simple/Mid | Qwen3 30B or 480B (Bedrock) |
| "Analyze race conditions in concurrent hash map with CAS" | Complex | Qwen 3.6 Plus (OpenRouter) |
| Large context (>256K tokens) | Context overflow | Qwen 3.6 Plus (OpenRouter) |

---

## Step 6: Connect OpenCode

### Option A: Global configuration (recommended)

If you don't want to copy `opencode.json` into every project, add the provider to
your global config at `~/.config/opencode/opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "nadirclaw": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "NadirClaw Router",
      "options": {
        "baseURL": "http://127.0.0.1:4000/v1",
        "apiKey": "local"
      },
      "models": {
        "auto": {
          "name": "Auto (3-tier: Qwen3 30B / 480B / 3.6 Plus)",
          "tool_call": true,
          "cost": { "input": 0.3, "output": 1.2, "cache_read": 0.05 },
          "limit": { "context": 262144, "output": 16384 }
        },
        "eco": {
          "name": "Budget (Qwen3 Coder 30B)",
          "tool_call": true,
          "cost": { "input": 0.15, "output": 0.60, "cache_read": 0.03 },
          "limit": { "context": 32768, "output": 16384 }
        },
        "premium": {
          "name": "Premium (Qwen 3.6 Plus 1M)",
          "reasoning": true,
          "tool_call": true,
          "cost": { "input": 0.0, "output": 0.0, "cache_read": 0.0 },
          "limit": { "context": 1048576, "output": 65536 }
        }
      }
    }
  }
  // ... other global settings (mcp, plugins, etc.)
}
```

Then start OpenCode from any project directory — the NadirClaw provider is always available.

### Option B: Per-project configuration

Create an `opencode.json` in the project root with the same `provider` block above,
then start OpenCode in that directory:

```bash
# Install OpenCode if needed
npm install -g opencode

# Start in project directory (picks up opencode.json automatically)
opencode
```

### Option C: Manual configuration (OpenCode)

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
| `eco` | Qwen3 Coder 30B (Bedrock) | Force cheap model |
| `premium` | Qwen 3.6 Plus (OpenRouter, 1M ctx) | Force best model / large context |

### Option D: Goose (recommended for small-context models)

[Goose](https://github.com/block/goose) is a terminal-based AI coding agent by Block that uses ~1K tokens of overhead per request vs OpenCode's ~180K+. This makes it work reliably with models that have 128-200K context limits (MiniMax M2.1, GLM 4.7).

**Why Goose over OpenCode?** OpenCode injects ~180-195K tokens of system prompt and tool definitions on every request ([anomalyco/opencode#17482](https://github.com/anomalyco/opencode/issues/17482), [#9461](https://github.com/anomalyco/opencode/issues/9461)). This exceeds the context limit of most models available on Bedrock Mantle, causing every request to fail with `BadRequestError: context length exceeded`. Goose sends ~1K tokens for the same request — a 99.4% reduction.

| Client | Prompt tokens ("say hello") | With recipe loaded | Works with 196K models? |
|---|---|---|---|
| OpenCode | ~180,000 | ~235,000 (with skills) | No (context overflow) |
| Goose | ~1,000 | ~2,200 | Yes |

#### Install Goose CLI (Windows)

```bash
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash
```

This installs to `~/goose/goose.exe`. The interactive config wizard may fail in non-interactive shells — configure manually instead (see below).

#### Configure NadirClaw as provider

**Option 1: Shell environment (Git Bash / terminal)**

Add to `~/.bashrc`:

```bash
export OPENAI_HOST=http://127.0.0.1:4000
export OPENAI_API_KEY=local
export GOOSE_PROVIDER=openai
export GOOSE_MODEL=auto
export GOOSE_MAX_TOKENS=16384
export PATH="$HOME/goose:$PATH"
```

**Option 2: Windows system environment (VS Code extension, Desktop app)**

The VS Code extension and Desktop app don't read `.bashrc`. Set Windows user environment variables with `setx` (requires `MSYS_NO_PATHCONV=1` in Git Bash to prevent path mangling):

```bash
MSYS_NO_PATHCONV=1 /c/Windows/System32/cmd.exe /c "setx GOOSE_PROVIDER openai"
MSYS_NO_PATHCONV=1 /c/Windows/System32/cmd.exe /c "setx GOOSE_MODEL auto"
MSYS_NO_PATHCONV=1 /c/Windows/System32/cmd.exe /c "setx OPENAI_HOST http://127.0.0.1:4000"
MSYS_NO_PATHCONV=1 /c/Windows/System32/cmd.exe /c "setx OPENAI_API_KEY local"
MSYS_NO_PATHCONV=1 /c/Windows/System32/cmd.exe /c "setx GOOSE_MAX_TOKENS 16384"
```

The `GOOSE_MAX_TOKENS` setting is critical — without it, the model may hit a low default token limit mid-response, get cut off without completing a tool call, and Goose assumes the task is done ([block/goose#7773](https://github.com/block/goose/issues/7773)). Set it to at least 16384.

Restart VS Code after setting these — `setx` only affects new processes.

#### Usage

```bash
# Interactive session
goose session

# One-shot command
goose run --text "explain this codebase"

# Force a specific model profile
goose run --model eco --text "quick question"
goose run --model premium --text "complex architecture review"

# Run with a recipe (skill)
goose run --recipe brainstorming --params "input=describe your idea"

# List available recipes
goose recipe list
```

**Model profiles:** Same as OpenCode — `auto`, `eco`, `premium` via `--model` flag or `GOOSE_MODEL`.

#### VS Code Extension

Install the [Goose VS Code extension](https://marketplace.visualstudio.com/items?itemName=block.goose-vscode) from the marketplace. After setting the Windows env vars above and restarting VS Code, the extension routes through NadirClaw automatically.

Verify by checking NadirClaw logs after sending a message:

```bash
docker logs nadirclaw --tail 10 | grep -v health
# Should show: POST /v1/chat/completions 200 OK
```

**Known issue:** The VS Code extension ignores `GOOSE_MODEL` and hardcodes `gpt-4o-mini` as the model name ([block/goose#8264](https://github.com/block/goose/issues/8264)). NadirClaw has a workaround: model aliases in `routing.py` map `gpt-4o-mini` → `openai/minimax.minimax-m2.1` and `gpt-4o` → `openai/zai.glm-4.7`. This is patched in the Docker build. Remove these aliases when the Goose issue is fixed.

#### Goose config file

Goose stores its config at `%APPDATA%\Block\goose\config\config.yaml` (Windows) or `~/.config/goose/config.yaml` (Linux/Mac). This file contains extension settings only — provider credentials are handled via environment variables and OS keyring.

#### Converting OpenCode skills to Goose recipes

OpenCode skills (SKILL.md files) can be converted to Goose recipes (YAML files) using the included converter script. The SKILL.md body becomes the recipe's `instructions` field.

```bash
# Convert all skills (one-time, or re-run when skills are updated)
python scripts/convert_skills_to_recipes.py \
  ~/.config/opencode/skills \
  ~/AppData/Roaming/Block/goose/config/recipes

# On Linux/Mac:
python scripts/convert_skills_to_recipes.py \
  ~/.config/opencode/skills \
  ~/.config/goose/recipes
```

The converter:
- Parses YAML frontmatter (`name`, `description`) → recipe `title`/`description`
- Converts markdown body → recipe `instructions`
- Adds a `{{ input }}` parameter for headless mode
- Skips malformed SKILL.md files (36 of 1824 skipped)

**Result:** 1,534 unique recipes in `%APPDATA%\Block\goose\config\recipes\`. List them with `goose recipe list`.

#### NadirClaw Usage Extension

A custom Goose MCP extension that provides in-session token usage, cost tracking, and budget status by reading NadirClaw's request logs.

**Tools provided:**

| Tool | Description |
|---|---|
| `usage_summary` | Token usage and cost breakdown by model/tier for last N hours |
| `budget_status` | Daily and monthly budget remaining vs limits |
| `recent_requests` | Last N requests with model, tokens, cost, latency |

**Setup:**

The extension is registered in `%APPDATA%\Block\goose\config\config.yaml`:

```yaml
extensions:
  nadirclaw-usage:
    enabled: true
    type: stdio
    name: NadirClaw Usage
    cmd: python
    args:
      - C:\Users\YOUR_USER\programmazione\aws-model-runner\scripts\goose_usage_extension.py
    description: Token usage, cost tracking, and budget status from NadirClaw proxy
    timeout: 30
```

**Requires:** NadirClaw logs mounted from Docker to host (`~/.nadirclaw/logs/`). This is configured in `docker-compose.yml`:

```yaml
volumes:
  - "${HOME}/.nadirclaw/logs:/root/.nadirclaw/logs"
```

**Usage in session:** Ask goose "show my token usage" or "what's my budget status" and it will call the tools automatically. Or call directly: "use the usage_summary tool for the last 24 hours".

**Cost estimation:** Bedrock Mantle doesn't return pricing in API responses, so the extension estimates costs from a built-in pricing table (`MODEL_PRICING` dict in the script). Update the table when models or pricing change. Costs are per-million-tokens estimates, not exact Bedrock billing.

Source: [scripts/goose_usage_extension.py](../scripts/goose_usage_extension.py)

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
# Docker: stop the container
pixi run -e dev down

# Or find and kill the process manually
netstat -ano | grep :4000
taskkill /F /PID <PID>    # Windows
kill <PID>                 # Linux/Mac
```

### Docker: container keeps restarting

Check logs for errors:

```bash
docker logs nadirclaw
```

Common causes:

- AWS credentials not configured (`~/.aws/` is mounted read-only into the container)
- Missing model access in Bedrock console

### "All configured models are currently unavailable" (OpenCode)

There are three known causes for this error. Check NadirClaw logs (`docker logs nadirclaw`) to identify which one.

#### Cause 1: NadirClaw optimizer strips tool fields

NadirClaw's `optimize_messages()` rebuilds messages as `{"role", "content"}` only, dropping `tool_calls` and `tool_call_id`. Bedrock rejects the malformed conversation with `BadRequestError: missing field tool_call_id`.

**Symptoms:** First message works, every subsequent message with tool results fails. All models in the fallback chain exhaust instantly (<2s).

**Fix:** Disable optimization in `config/nadirclaw.env`:

```bash
NADIRCLAW_OPTIMIZE=off
```

**Upstream:** [NadirClaw issue — optimizer drops tool fields](https://github.com/NadirRouter/NadirClaw/issues)

#### Cause 2: NadirClaw sends `content: null` on tool-call messages

When an assistant message has only `tool_calls` (no text), `text_content()` returns `""` but a falsy check converts it to `None`. Bedrock/Mantle rejects `content: null`.

**Fix:** Patched in the Dockerfile with `sed`:

```dockerfile
RUN sed -i 's/content = text if text else message.content/content = text if text is not None else message.content/g' \
    /usr/local/lib/python3.11/site-packages/nadirclaw/server.py
```

#### Cause 3: OpenCode skill descriptions bloat the system prompt

The `opencode-agent-skills` plugin eagerly injects ALL skill descriptions (`<available-skills>`) on session start and runs semantic matching (HuggingFace embeddings) on every message. With 1,800+ skills this is ~235KB per request, exceeding model context limits.

**Fix:** Use a patched local clone of the plugin with eager injection disabled:

```bash
# Clone and patch the plugin (one-time)
cd ~/.config/opencode
git clone https://github.com/joshuadavidthomas/opencode-agent-skills.git opencode-agent-skills-local
cd opencode-agent-skills-local && npm install

# Apply the lazy-loading patch to src/plugin.ts:
# 1. Remove the getSkillSummaries() and precomputeSkillEmbeddings() calls at init
# 2. Replace the eager injectSkillsList() call with a no-op (just mark session as set up)
# 3. Remove the per-message matchSkills() semantic matching block
# 4. Remove the post-compaction re-injection in the event handler
# See the patched file for exact changes.
```

Create the plugin entry point at `~/.config/opencode/plugin/skills.ts`:

```typescript
export { SkillsPlugin as default } from "../opencode-agent-skills-local/src/plugin";
```

Remove `opencode-agent-skills` from the `"plugin"` array in `opencode.json` — the local plugin auto-loads from the `plugin/` directory.

**To update:** `cd ~/.config/opencode/opencode-agent-skills-local && git pull`, then re-apply the patch to `src/plugin.ts` (the 4 changes above).

**Upstream:** [anomalyco/opencode#13188](https://github.com/anomalyco/opencode/issues/13188)

#### Cause 4: LiteLLM missing model support

LiteLLM may not have newer Bedrock models (e.g., `zai.glm-5`) in its registry. The `bedrock/converse/` fallback route doesn't support tool definitions.

**Fix:** Use Bedrock Mantle (OpenAI-compatible endpoint) instead of native Bedrock SDK:

```bash
# In config/nadirclaw.env:
NADIRCLAW_API_BASE=https://bedrock-mantle.eu-west-2.api.aws/v1
NADIRCLAW_COMPLEX_MODEL=openai/zai.glm-5  # not bedrock/zai.glm-5
```

**Upstream:** [BerriAI/litellm#24993](https://github.com/BerriAI/litellm/issues/24993)

#### Cause 5: Model calls native `skill` tool instead of plugin tools

OpenCode's built-in `skill` tool only knows about native skills (~5 from `~/.agents/skills/`). Plugin-discovered skills (1,800+ from `~/.config/opencode/skills/`) can only be loaded via the plugin's `use_skill` tool, but models default to the native tool.

**Fix:** Add a global instruction file at `~/.config/opencode/AGENTS.md`:

```markdown
# Skill Plugin Workflow

When working with skills, use the **plugin tools** (`get_available_skills`,
`use_skill`, `read_skill_file`, `run_skill_script`), NOT the native `skill` tool.

Skills found by `get_available_skills` can ONLY be loaded with `use_skill`.
```

#### Cause 6: OpenCode shows 0 tokens / $0.00 spent

Two separate issues cause the context meter and cost display to show zeros.

**Missing model pricing:** OpenCode can't calculate costs for custom provider models unless `cost` fields are configured. Add `cost` ($/million tokens) and `limit` to each model in `opencode.json` — see the config example in [Step 6](#step-6-connect-opencode).

**Streaming responses return zero token counts:** NadirClaw's LiteLLM streaming path has two bugs:

1. The `acompletion()` call sets `stream: True` but doesn't pass `stream_options: {"include_usage": True}`, so the upstream provider never includes token counts in streaming chunks.
2. Some providers send a final usage-only chunk with empty `choices`. The `if choice is None: continue` guard drops it before usage is extracted.

**Fix:** Patched in the Dockerfile (lines 13-19). Remove these patches when [NadirClaw PR #33](https://github.com/NadirRouter/NadirClaw/pull/33) is merged upstream.

**Verify:** After rebuilding the container, test streaming usage:

```bash
curl -s http://127.0.0.1:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local" \
  -d '{"model":"eco","messages":[{"role":"user","content":"hi"}],"max_tokens":5,"stream":true,"stream_options":{"include_usage":true}}'
```

The final SSE chunk should show non-zero `prompt_tokens` and `completion_tokens`.

#### Cause 7: "All configured models are currently unavailable" with small prompts

OpenCode sends ~180-195K tokens of system prompt + tool definitions with every request, even for simple messages. This exceeds the context limit of most models (MiniMax M2.1: 196K, GLM 4.7: 202K), causing all models in the fallback chain to fail with `BadRequestError: context length exceeded`.

NadirClaw has a patch that auto-clamps `max_tokens` on context overflow, but this doesn't help when the **input tokens alone** exceed the model's context limit.

**Symptoms:** NadirClaw logs show:

```
Pre-content streaming error: You passed 180225 input tokens and requested 8192 output tokens.
However, the model's context length is only 196608 tokens.
```

**Fix options:**

1. **Use models with larger context** — GLM-5 (1M context) or DeepSeek V3.2 (128K but may handle tool defs differently)
2. **Reduce OpenCode tool count** — Create a minimal agent with fewer tools:
   ```json
   {
     "agent": {
       "lite": {
         "tools": ["bash", "read", "write", "edit", "glob", "grep"],
         "prompt": ".opencode/agents/lite.md"
       }
     }
   }
   ```
3. **Wait for OpenCode fix** — [anomalyco/opencode#13188](https://github.com/anomalyco/opencode/issues/13188) tracks system prompt reduction

#### General notes

**After changing `config/nadirclaw.env`**, you must do a full restart (not just `docker compose restart`):

```bash
pixi run -e dev down && pixi run -e dev up
```

### Docker: `docker compose restart` does not reload config

Docker Compose only reads `env_file` during container creation (`up`), not on `restart`. Always use:

```bash
docker compose down && docker compose up -d
# Or: pixi run -e dev down && pixi run -e dev up
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

To stop NadirClaw:

```bash
# Docker
pixi run -e dev down

# Direct
# Close the terminal or Ctrl+C
```

---

## Alternative Models

Available on AWS Bedrock Mantle and OpenRouter, usable as drop-in replacements. Use `NADIRCLAW_MODEL_API_BASES` to route models to different providers/regions.

| Model ID | Provider | Params | Context | Notes |
|---|---|---|---|---|
| `qwen.qwen3-coder-30b-a3b-v1:0` | Bedrock | 30B MoE | 32K | **Budget tier (default)** |
| `qwen.qwen3-coder-480b-a35b-v1:0` | Bedrock | 480B MoE | 256K | **Mid tier (default)** |
| `qwen/qwen3.6-plus-preview` | OpenRouter | N/A | 1M | **Premium tier (default)** — free in preview |
| `qwen.qwen3-coder-next` | Bedrock | N/A | 128K | Mid alternative, unbenched |
| `moonshotai.kimi-k2.5` | Bedrock | 1T | 128K | Fallback — strong agentic tool discipline |
| `deepseek.v3.2` | Bedrock | 685B MoE | 64K | Fallback — strong all-rounder |
| `zai.glm-5` | Bedrock | 744B | 1M | Alternative premium (us-west-1 only) |
| `zai.glm-4.7` | Bedrock | 355B | 202K | Fallback — top leaderboard |
| `minimax.minimax-m2.1` | Bedrock | N/A | 196K | Budget fallback |
| `qwen.qwen3-next-80b-a3b` | Bedrock | 80B MoE | 128K | Compact, fast |

> **Note:** Qwen 3.6 Plus is free on OpenRouter during preview. When it becomes available on Bedrock, switch `NADIRCLAW_COMPLEX_MODEL` to the Bedrock model ID to avoid the OpenRouter dependency.

---

## References

- [NadirClaw](https://github.com/NadirRouter/NadirClaw) — open-source model router
- [OpenCode](https://opencode.ai/) — open-source AI coding assistant
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Onyx Open LLM Leaderboard](https://onyx.app/open-llm-leaderboard) — model benchmarks
- [Tailscale](https://tailscale.com/) — zero-config VPN
- [AWS CDK](https://docs.aws.amazon.com/cdk/) — infrastructure as code