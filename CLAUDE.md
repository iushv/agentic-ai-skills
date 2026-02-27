# Claude Code — Agentic AI Skills

@AGENTS.md

## Claude-Specific Configuration

### Model IDs

- **Primary**: `claude-sonnet-4-6` (best balance of quality and speed)
- **Complex tasks**: `claude-opus-4-6` (highest capability)
- **Fast/cheap tasks**: `claude-haiku-4-5-20251001` (lowest latency)

### Available Skills

- `/agentic-design-review` — Review agentic code against blueprint rules
- `/agent-scaffold` — Generate production-ready agent skeleton
- `/tool-schema-design` — Design Pydantic tool schema from description
- `/agent-debug` — Diagnose failing agent via incident playbook
- `/guardrail-setup` — Add guardrail pipeline with tests

### Conventions

- Use async-first Python 3.12+.
- Use Pydantic v2 for all schemas.
- Use `httpx` for async HTTP. Never `requests` in async code.
- Prefer structured outputs over free-form text parsing.
