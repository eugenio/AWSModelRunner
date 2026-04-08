# AWS Model Runner - Project Conventions

## Overview
3-tier AI coding assistant router: NadirClaw proxy -> AWS Bedrock / OpenRouter backends.

## Package Manager
- **pixi** manages all dependencies and tasks.
- Run commands: `pixi run -e dev <task>` (see `pixi.toml` for available tasks).
- Never use pip directly.

## Code Quality Gates
- **Ruff**: `pixi run -e dev lint` — must pass before every commit.
- **Mypy**: `pixi run -e dev typecheck` — must pass before every commit.
- **Tests**: `pixi run -e dev test` — pytest, run before declaring work complete.
- **Docstring coverage**: `pixi run -e dev interrogate -v --fail-under 95 src/` — gate at 95%.

## Project Structure
```
src/              # Main package (currently __init__.py only)
scripts/          # Standalone scripts (setup, verify, goose extension, skill converter)
infra/            # CDK infrastructure code
config/           # NadirClaw YAML configs and model definitions
tests/            # pytest test suite
docs/             # Documentation (setup guide, analysis)
```

## Conventions
- Google-style docstrings for all public functions/classes.
- Type hints on all public interfaces.
- Tests use pytest with Arrange-Act-Assert pattern.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).

## Docker
- `docker compose up -d --build` to start NadirClaw locally.
- Config mounted from `config/` directory.
