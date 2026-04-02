# AWS Model Runner

Self-hosted, cost-optimized AI coding assistant with automatic 3-tier model routing on AWS Bedrock.

```
OpenCode --> NadirClaw (localhost) --> AWS Bedrock (eu-west-2)
                |
         Classifies prompt
         complexity (~10ms)
                |
         +------+------+
         v      v      v
       Simple   Mid   Complex
     Qwen 30B  480B  Kimi K2.5
```

NadirClaw classifies each prompt's complexity using a local sentence-embedding model and routes it to the cheapest model that can handle it. Simple tasks go to Qwen3 Coder 30B, complex tasks to Kimi K2.5.

## Why

- **No throttling** -- pay-per-use, no message caps or peak-hour limits
- **50% cheaper** than Claude Max 5x at heavy usage (~55 vs ~110 EUR/mo)
- **EU data residency** -- all inference in eu-west-2 (London)
- **Model flexibility** -- 6+ models, swap anytime
- **Open source** -- NadirClaw + OpenCode, fully auditable
- **Private** -- VPC endpoint + Tailscale, traffic never hits public internet

## Quick Start (Docker — recommended)

```bash
# 1. Install
pixi install

# 2. Deploy AWS infra (VPC, Bedrock endpoint, IAM)
cd infra && cdk deploy ModelRunnerNetwork ModelRunnerBedrock --require-approval never

# 3. Start NadirClaw in Docker (binds to 127.0.0.1:4000 only)
pixi run -e dev up

# 4. Verify
pixi run -e dev verify
```

Then connect OpenCode (picks up `opencode.json` automatically):

```bash
opencode
```

> **VS Code users:** The container starts automatically when you open this project (via `.vscode/tasks.json`).

### Without Docker

```bash
mkdir -p ~/.nadirclaw && cp config/nadirclaw.env ~/.nadirclaw/.env
pixi run -e dev start
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for the full step-by-step walkthrough.

## Models (eu-west-2)

| Tier | Model | Use Case |
|------|-------|----------|
| Budget | Qwen3 Coder 30B | Boilerplate, completions, Q&A, docstrings |
| Mid | Qwen3 Coder 480B | Code generation, refactoring, tests |
| Premium | Kimi K2.5 | Complex debugging, architecture, security review |

Also available as drop-in replacements: DeepSeek V3.1/V3.2, GLM-4.7, GLM-5, Qwen3 Coder Next.

## Cost (Solo Developer, incl. 20% VAT)

| Usage | Monthly (EUR) |
|-------|---------------|
| Light (30 req/day) | ~30-40 |
| Medium (80 req/day) | ~55-75 |
| Heavy (200 req/day) | ~80-120 |

See [AWS_Coding_Model_Cost_Security_Analysis.md](AWS_Coding_Model_Cost_Security_Analysis.md) for the full cost and security analysis with benchmark correlations.

## Commands

```bash
# Docker (recommended)
pixi run -e dev up         # Start NadirClaw container (127.0.0.1:4000)
pixi run -e dev down       # Stop container
pixi run -e dev logs       # Follow container logs

# Direct (without Docker)
pixi run -e dev start      # Start NadirClaw router directly

# Shared
pixi run -e dev verify     # Test all 3 model tiers
pixi run -e dev report     # Cost report by model
pixi run -e dev savings    # How much you saved vs all-premium
pixi run -e dev dashboard  # Live terminal dashboard
```

## Project Structure

```
aws-model-runner/
  Dockerfile                 # NadirClaw container image
  docker-compose.yml         # Localhost-only binding, healthcheck, AWS creds mount
  config/nadirclaw.env       # NadirClaw 3-tier routing config
  opencode.json              # OpenCode client config
  .vscode/tasks.json         # Auto-start container on folder open
  scripts/
    setup.py                 # Automated setup wizard
    verify_connection.py     # End-to-end connection test
  infra/                     # AWS CDK (Python)
    stacks/
      network_stack.py       # VPC + private subnets
      bedrock_stack.py       # VPC endpoint + IAM role
      tailscale_stack.py     # Tailscale subnet router (optional)
  AWS_Coding_Model_Cost_Security_Analysis.md  # Full analysis
  SETUP_GUIDE.md             # Step-by-step recipe
```

## Security

- VPC endpoint for Bedrock -- traffic stays on AWS backbone
- Tailscale subnet router -- encrypted WireGuard tunnel (optional)
- IMDSv2 enforced -- SSRF protection on EC2 instances
- iptables blocking 169.254.169.254 from forwarded traffic
- IAM least-privilege -- `bedrock:InvokeModel` restricted to 3 model ARNs
- CloudWatch prompt logging disabled -- prompts are not stored
- NadirClaw runs on localhost only -- Docker binds to 127.0.0.1:4000, not exposed to the network

## Known Issues

- **Kimi K2.5 and Qwen3 480B reject large system prompts** -- OpenCode sends ~600KB of system instructions + tool definitions. These models fail with `BadRequestError` on Bedrock. Qwen3 30B handles it. The fallback chain is configured so requests automatically fall through to 30B, but multi-turn conversations with accumulated tool results can exceed even 30B's limits.
- **`docker compose restart` does not reload `config/nadirclaw.env`** -- use `docker compose down && docker compose up -d` instead.

See [SETUP_GUIDE.md](SETUP_GUIDE.md#troubleshooting) for detailed troubleshooting.

## License

[MIT](LICENSE)