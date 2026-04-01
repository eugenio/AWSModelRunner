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

## Quick Start

```bash
# 1. Install
pixi install

# 2. Deploy AWS infra (VPC, Bedrock endpoint, IAM)
cd infra && cdk deploy ModelRunnerNetwork ModelRunnerBedrock --require-approval never

# 3. Configure NadirClaw
mkdir -p ~/.nadirclaw && cp config/nadirclaw.env ~/.nadirclaw/.env

# 4. Start
pixi run start

# 5. Verify
pixi run verify
```

Then connect OpenCode (picks up `opencode.json` automatically):

```bash
opencode
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
pixi run start       # Start NadirClaw router
pixi run verify      # Test all 3 model tiers
pixi run report      # Cost report by model
pixi run savings     # How much you saved vs all-premium
pixi run dashboard   # Live terminal dashboard
```

## Project Structure

```
aws-model-runner/
  config/nadirclaw.env       # NadirClaw 3-tier routing config
  opencode.json              # OpenCode client config
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
- NadirClaw runs on localhost only -- not exposed to the network

## License

[MIT](LICENSE)