# Agentic AI Skills

[![CI](https://github.com/iushv/agentic-ai-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/iushv/agentic-ai-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production rules and reusable skills for building agentic AI systems. Works as a
**contextual plugin** across Claude Code, Cursor, GitHub Copilot, OpenAI Codex,
Windsurf, and Aider — active only when you're building agentic AI.

## What's Inside

- **AGENTS.md** — Canonical production rules (architecture, tools, safety, reliability,
  observability, cost, testing).
- **5 Skills** — Reusable workflows for design review, scaffolding, tool design,
  debugging, and guardrail setup.
- **Two working generators** — `agent-scaffold` and `guardrail-setup` are not prose.
  Each ships templates and a script that emit runnable code whose test suite passes
  offline.
- **Evals** — 15 graded test cases (3 per skill) so skill changes are measured, not
  guessed at.
- **Auto-sync** — One script generates contextual rule files for every supported tool.

## Scaffold an agent

```bash
python skills/agent-scaffold/scripts/scaffold.py \
  --name analytics_agent --out ./analytics_agent \
  --tools run_sql,create_chart \
  --description "answers business questions over the analytics warehouse"

cd analytics_agent && pip install -e '.[dev]' && pytest
```

That produces 20 files — ReAct loop, budget config, six-layer guardrail pipeline,
retry with circuit breaker and model fallback, structured tracing, and 68 tests
that drive the real loop against a fake model. No API key needed to run them.

## Harden an existing agent

```bash
python skills/guardrail-setup/scripts/add_guardrails.py \
  --out ./myproject/guardrails --sql --files

pytest ./myproject/guardrails
```

That drops in a six-layer pipeline: schema validation, injection patterns, an ML
classifier seam, semantic intent checks, per-tool guards, and output scrubbing.
Layer 5 guards are opt-in per risk — SQL, filesystem, code execution — so you
get 13 files and 53 tests minimally, or 19 files and 108 tests with everything.
The tests need only `pytest` and `pydantic`.

CI runs both generators on every push — generating, byte-compiling, and running
the emitted test suites, the guardrail package in both its minimal and
fully-armed configurations — so the templates cannot rot silently.

## Quick Start

```bash
# Copy the agentic-ai-skills/ directory into your project
cp -r agentic-ai-skills/ your-project/agentic-ai-skills/

# Generate tool-specific rule files at your project root
bash your-project/agentic-ai-skills/scripts/sync-rules.sh

# Verify everything is correct
bash your-project/agentic-ai-skills/validate.sh
```

## Installation by Tool

### Claude Code

Skills use the **plugin directory format** (`<plugin>/skills/<name>/SKILL.md`).

**Install as a plugin** (recommended):

```
/plugin marketplace add iushv/agentic-ai-skills
/plugin install agentic-ai-skills@agentic-ai-skills
```

**Auto-discovery** (default): Skills are auto-discovered when working inside the
`agentic-ai-skills/` directory. `CLAUDE.md` is lazy-loaded in the same context —
no root pollution.

**Project-level mirror**: Run `sync-rules.sh --tools claude` to mirror skills to
`<root>/.claude/skills/*/SKILL.md` for project-wide discovery.

**Plugin mode**: Use directly as a plugin:
```bash
claude --plugin-dir ./agentic-ai-skills
```

**Opt-in always-on**: Add `@agentic-ai-skills/AGENTS.md` to your root `CLAUDE.md`
if you want rules active in every session.

> This package **never generates or modifies** your root `CLAUDE.md`.

### Cursor

Rules use `alwaysApply: false` (**Apply Intelligently** mode). Cursor's model reads
the description and decides when to include the rules based on your current task.

```bash
bash agentic-ai-skills/scripts/sync-rules.sh --tools cursor
# Generates: <root>/.cursor/rules/agentic-ai.mdc
```

You can also `@`-reference the rule manually in any Cursor chat.

### Windsurf

Rules use `trigger: model_decision` — Cascade applies them only when relevant to
your current task. Not injected into every conversation.

```bash
bash agentic-ai-skills/scripts/sync-rules.sh --tools windsurf
# Generates: <root>/.windsurf/rules/agentic-ai.md
```

### GitHub Copilot

Instructions are scoped via `applyTo` glob to agent-related filenames. Only activates
when editing files matching `**/agent*`, `**/tool*`, `**/guardrail*`, etc.

```bash
bash agentic-ai-skills/scripts/sync-rules.sh --tools copilot
# Generates: <root>/.github/instructions/agentic-ai.instructions.md
```

### OpenAI Codex

Skills are mirrored to `<root>/.agents/skills/*/SKILL.md` (byte-identical copies).
Codex auto-discovers them via lazy metadata-first loading.

```bash
bash agentic-ai-skills/scripts/sync-rules.sh --tools codex
# Generates: <root>/.agents/skills/*/SKILL.md
```

### Aider

Manual only — Aider has no plugin system.

```bash
aider --read agentic-ai-skills/AGENTS.md
```

Or add to `.aider.conf.yml`:

```yaml
read:
  - agentic-ai-skills/AGENTS.md
```

## Skills Reference

| Skill | Command | Purpose | Ships code |
|-------|---------|---------|---|
| `agentic-design-review` | `/agentic-design-review` | Review agentic code against blueprint rules | |
| `agent-scaffold` | `/agent-scaffold` | Generate production-ready agent skeleton | ✅ generator |
| `tool-schema-design` | `/tool-schema-design` | Design Pydantic tool schema from description | |
| `agent-debug` | `/agent-debug` | Diagnose failing agent via incident playbook | |
| `guardrail-setup` | `/guardrail-setup` | Add guardrail pipeline with tests | ✅ generator |

## Evals

Each skill ships an eval set at `skills/<name>/evals/evals.json` — three graded cases
covering the skill's main paths, written against the schema Anthropic's `skill-creator`
uses. Every case pairs a realistic prompt with concrete, checkable expectations rather
than a subjective quality bar:

```json
{
  "id": 1,
  "prompt": "My agent keeps hitting max_iterations. It calls search_docs with the same query eight times.",
  "expectations": [
    "The report categorises the failure as a loop",
    "The root cause names the tool returning unhelpful or unchanging output"
  ]
}
```

The rules in `AGENTS.md` require an eval gate before merging a prompt or tool change.
These exist so this package holds itself to that same bar — run them after editing any
`SKILL.md` and treat a drop in pass rate as a regression.

## Keeping Rules in Sync

`AGENTS.md` is the single source of truth. After editing it:

```bash
# Regenerate all tool-specific files
bash agentic-ai-skills/scripts/sync-rules.sh

# Regenerate only specific tools
bash agentic-ai-skills/scripts/sync-rules.sh --tools cursor,codex

# Verify parity (useful in CI)
bash agentic-ai-skills/scripts/sync-rules.sh --check

# Scoped check
bash agentic-ai-skills/scripts/sync-rules.sh --tools cursor --check

# Run full validation suite
bash agentic-ai-skills/validate.sh

# Scoped validation
bash agentic-ai-skills/validate.sh --tools cursor

# Clean up stale generated files from old format
bash agentic-ai-skills/scripts/sync-rules.sh --clean-stale
```

### What `sync-rules.sh` generates

| Source | Target (at project root) | Tool | Activation |
|--------|--------------------------|------|------------|
| `skills/*/` | `<root>/.claude/skills/*/` | Claude Code | Auto-discovered, lazy-loaded |
| `skills/*/` | `<root>/.agents/skills/*/` | Codex | Lazy metadata-first |
| `AGENTS.md` | `<root>/.cursor/rules/agentic-ai.mdc` | Cursor | `alwaysApply: false` (model decides) |
| `AGENTS.md` | `<root>/.windsurf/rules/agentic-ai.md` | Windsurf | `trigger: model_decision` |
| `AGENTS.md` | `<root>/.github/instructions/agentic-ai.instructions.md` | Copilot | `applyTo` glob |

### What `validate.sh` checks

1. `AGENTS.md` ≤ 200 lines
2. Each `SKILL.md` ≤ 500 lines
3. SKILL.md frontmatter has `name` and `description`
4. No absolute local paths in any file
5. Generated files match canonical source
6. Skill mirrors match the canonical directory, bundled resources included
7. Mirror frontmatter integrity (starts with `---`)
8. Generated rule frontmatter schema (tool-specific keys)
9. CLAUDE.md safety audit (sync script never references root CLAUDE.md)
10. Bundled Python scripts parse

## Project Structure

```
your-project/
├── agentic-ai-skills/                       # The skills package (plugin format)
│   ├── README.md
│   ├── LICENSE
│   ├── AGENTS.md                            # Canonical rules (edit this)
│   ├── CLAUDE.md                            # Claude Code project memory
│   ├── .claude-plugin/
│   │   ├── plugin.json                      # Plugin manifest
│   │   └── marketplace.json                 # Marketplace entry
│   ├── .github/workflows/ci.yml             # Runs sync + validate on every push
│   ├── skills/
│   │   ├── agentic-design-review/
│   │   │   ├── SKILL.md                     # Canonical skill source
│   │   │   └── evals/evals.json             # Graded test cases
│   │   ├── agent-scaffold/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/scaffold.py          # The generator
│   │   │   ├── assets/                      # Templates it renders
│   │   │   └── evals/evals.json
│   │   ├── guardrail-setup/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/add_guardrails.py
│   │   │   ├── assets/                      # Templates it renders
│   │   │   └── evals/evals.json
│   │   ├── tool-schema-design/
│   │   └── agent-debug/
│   ├── scripts/sync-rules.sh               # Generates tool-specific files
│   └── validate.sh                          # Pre-publish checks
│
├── .claude/skills/*/SKILL.md                # Mirrors (Claude Code discovery)
├── .agents/skills/*/SKILL.md                # Mirrors (Codex discovery)
├── .cursor/rules/agentic-ai.mdc            # Generated (contextual)
├── .windsurf/rules/agentic-ai.md           # Generated (contextual)
└── .github/instructions/agentic-ai.instructions.md  # Generated (scoped)
```
