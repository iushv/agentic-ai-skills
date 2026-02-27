# Agentic AI Skills

Production rules and reusable skills for building agentic AI systems. Works across
**Claude Code, Cursor, GitHub Copilot, OpenAI Codex, Windsurf, and Aider**.

## What's Inside

- **AGENTS.md** — Canonical production rules (architecture, tools, safety, reliability,
  observability, cost, testing).
- **5 Skills** — Reusable workflows for design review, scaffolding, tool design,
  debugging, and guardrail setup.
- **Auto-sync** — One script generates rule files for every supported tool.

## Quick Start

```bash
# Clone or copy the agentic-ai-skills/ directory into your project
cp -r agentic-ai-skills/ your-project/agentic-ai-skills/

# Generate tool-specific rule files
cd agentic-ai-skills && bash scripts/sync-rules.sh

# Verify everything is correct
bash validate.sh
```

## Installation by Tool

### Claude Code

Claude Code reads `CLAUDE.md` and `skills/*/SKILL.md` natively.

1. Copy `agentic-ai-skills/` into your project root.
2. Claude Code auto-discovers `CLAUDE.md` (which imports `AGENTS.md` via `@AGENTS.md`).
3. Skills are available as `/agentic-design-review`, `/agent-scaffold`, etc.

### Cursor

Cursor reads `.cursor/rules/*.mdc` files.

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. The rules appear in `.cursor/rules/agentic-ai.mdc` (always-apply).

### GitHub Copilot

Copilot reads `.github/copilot-instructions.md`.

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. The rules appear in `.github/copilot-instructions.md`.

### OpenAI Codex

Codex reads `AGENTS.md` and `skills/*/SKILL.md` natively (same format as Claude Code).

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. Codex reads `.codex/AGENTS.md` and the skill files.

### Windsurf

Windsurf reads `.windsurfrules` at project root.

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. The rules appear in `.windsurfrules`.

### Aider

Aider reads any markdown file passed via `--read`.

```bash
aider --read agentic-ai-skills/AGENTS.md
```

Or add to `.aider.conf.yml`:

```yaml
read:
  - agentic-ai-skills/AGENTS.md
```

## Skills Reference

| Skill | Command | Purpose |
|-------|---------|---------|
| `agentic-design-review` | `/agentic-design-review` | Review agentic code against blueprint rules |
| `agent-scaffold` | `/agent-scaffold` | Generate production-ready agent skeleton |
| `tool-schema-design` | `/tool-schema-design` | Design Pydantic tool schema from description |
| `agent-debug` | `/agent-debug` | Diagnose failing agent via incident playbook |
| `guardrail-setup` | `/guardrail-setup` | Add guardrail pipeline with tests |

## Keeping Rules in Sync

`AGENTS.md` is the single source of truth. After editing it:

```bash
# Regenerate all tool-specific files
bash scripts/sync-rules.sh

# Verify parity (useful in CI)
bash scripts/sync-rules.sh --check

# Run full validation suite
bash validate.sh
```

### What `sync-rules.sh` generates

| Source | Target | Tool |
|--------|--------|------|
| `AGENTS.md` | `.cursor/rules/agentic-ai.mdc` | Cursor |
| `AGENTS.md` | `.github/copilot-instructions.md` | GitHub Copilot |
| `AGENTS.md` | `.windsurfrules` | Windsurf |
| `AGENTS.md` | `.codex/AGENTS.md` | OpenAI Codex |

### What `validate.sh` checks

- `AGENTS.md` ≤ 180 lines.
- Each `SKILL.md` ≤ 500 lines.
- SKILL.md frontmatter has `name` and `description`.
- No local paths (`/Users/`, `/home/`, `C:\`) in any file.
- Generated files match canonical source.

## Project Structure

```
agentic-ai-skills/
├── README.md
├── AGENTS.md                    # Canonical rules (edit this)
├── CLAUDE.md                    # Claude Code project memory
├── skills/
│   ├── agentic-design-review/SKILL.md
│   ├── agent-scaffold/SKILL.md
│   ├── tool-schema-design/SKILL.md
│   ├── agent-debug/SKILL.md
│   └── guardrail-setup/SKILL.md
├── .cursor/rules/agentic-ai.mdc       # Generated
├── .github/copilot-instructions.md     # Generated
├── .windsurfrules                      # Generated
├── .codex/AGENTS.md                    # Generated
├── scripts/sync-rules.sh              # Generates tool-specific files
└── validate.sh                        # Pre-publish checks
```
