# Claude Code — Agentic AI Skills

@AGENTS.md

## Plugin Format

This package follows Claude Code's **plugin directory structure**:
- Skills live at `skills/*/SKILL.md` (plugin format: `<plugin>/skills/<name>/SKILL.md`)
- Usable directly via `claude --plugin-dir ./agentic-ai-skills`
- `sync-rules.sh` mirrors skills to `<root>/.claude/skills/` for project-level discovery

**Root CLAUDE.md is never generated or modified by any script in this package.**

## Claude-Specific Configuration

### Model IDs

- **Primary**: `claude-sonnet-5` (best balance of quality and speed)
- **Complex tasks**: `claude-opus-5` (highest capability)
- **Fast/cheap tasks**: `claude-haiku-4-5` (lowest latency)

Use model aliases, never date-suffixed IDs. Control reasoning depth with
adaptive thinking (`thinking={"type": "adaptive"}`) plus `output_config.effort`
— fixed `budget_tokens` is removed on current models and returns a 400.

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
