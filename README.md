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
# Clone or copy the agentic-ai-skills/ directory into your project root
cp -r agentic-ai-skills/ your-project/agentic-ai-skills/

# Generate tool-specific rule files at your project root
bash your-project/agentic-ai-skills/scripts/sync-rules.sh

# Verify everything is correct
bash your-project/agentic-ai-skills/validate.sh
```

The sync script auto-detects the project root (parent of `agentic-ai-skills/`) and
writes generated files there (e.g., `.cursor/rules/`, `.github/`, `.windsurfrules`)
so each tool discovers them at the expected location.

## Installation by Tool

### Claude Code

Claude Code reads `CLAUDE.md` and `skills/*/SKILL.md` natively.

1. Copy `agentic-ai-skills/` into your project root.
2. Claude Code auto-discovers `CLAUDE.md` (which imports `AGENTS.md` via `@AGENTS.md`).
3. Skills are available as `/agentic-design-review`, `/agent-scaffold`, etc.

### Cursor

Cursor reads `.cursor/rules/*.mdc` files at the repo root.

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. The rules appear in `<project-root>/.cursor/rules/agentic-ai.mdc` (always-apply).

### GitHub Copilot

Copilot reads `.github/copilot-instructions.md` at the repo root.

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. The rules appear in `<project-root>/.github/copilot-instructions.md`.

### OpenAI Codex

Codex reads `AGENTS.md` and `skills/*/SKILL.md` natively (same format as Claude Code).

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. Codex reads `<project-root>/.codex/AGENTS.md` and the skill files.

### Windsurf

Windsurf reads `.windsurfrules` at the repo root.

1. Copy `agentic-ai-skills/` into your project root.
2. Run `bash agentic-ai-skills/scripts/sync-rules.sh`.
3. The rules appear in `<project-root>/.windsurfrules`.

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
# Regenerate all tool-specific files (writes to project root)
bash agentic-ai-skills/scripts/sync-rules.sh

# Verify parity (useful in CI)
bash agentic-ai-skills/scripts/sync-rules.sh --check

# Run full validation suite
bash agentic-ai-skills/validate.sh
```

### What `sync-rules.sh` generates

| Source | Target (at project root) | Tool |
|--------|--------------------------|------|
| `AGENTS.md` | `<root>/.cursor/rules/agentic-ai.mdc` | Cursor |
| `AGENTS.md` | `<root>/.github/copilot-instructions.md` | GitHub Copilot |
| `AGENTS.md` | `<root>/.windsurfrules` | Windsurf |
| `AGENTS.md` | `<root>/.codex/AGENTS.md` | OpenAI Codex |

### What `validate.sh` checks

- `AGENTS.md` ≤ 180 lines.
- Each `SKILL.md` ≤ 500 lines.
- SKILL.md frontmatter has `name` and `description`.
- No absolute local paths (macOS, Linux, or Windows home directories) in any file.
- Generated files match canonical source.

## Project Structure

```
your-project/
├── agentic-ai-skills/                       # The skills package
│   ├── README.md
│   ├── AGENTS.md                            # Canonical rules (edit this)
│   ├── CLAUDE.md                            # Claude Code project memory
│   ├── skills/
│   │   ├── agentic-design-review/SKILL.md
│   │   ├── agent-scaffold/SKILL.md
│   │   ├── tool-schema-design/SKILL.md
│   │   ├── agent-debug/SKILL.md
│   │   └── guardrail-setup/SKILL.md
│   ├── scripts/sync-rules.sh               # Generates tool-specific files
│   └── validate.sh                          # Pre-publish checks
│
├── .cursor/rules/agentic-ai.mdc            # Generated at project root
├── .github/copilot-instructions.md          # Generated at project root
├── .windsurfrules                           # Generated at project root
└── .codex/AGENTS.md                         # Generated at project root
```
