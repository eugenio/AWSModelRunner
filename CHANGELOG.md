# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `interrogate` and `types-PyYAML` dev dependencies
- Project CLAUDE.md with repo-specific conventions
- Pre-commit hook with gitleaks secret scanning

### Fixed
- Ruff lint errors (unused variable, import order)
- Mypy stub for PyYAML

## [0.1.0] - 2026-03-25

### Added
- 3-tier AI coding assistant router with NadirClaw + AWS Bedrock + Tailscale
- Docker-first workflow with localhost-only binding
- CDK infrastructure for AWS deployment
- Goose MCP integration with usage extension
- Qwen3 Coder + Qwen 3.6 Plus (OpenRouter) model lineup

### Fixed
- NadirClaw streaming to return real token counts
- LiteLLM fallback chain and LITELLM_MODIFY_PARAMS
- NadirClaw tool-use bugs with upstream references
