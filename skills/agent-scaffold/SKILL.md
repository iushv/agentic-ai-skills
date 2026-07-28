---
name: agent-scaffold
description: Generate a production-ready agent skeleton — agent loop, tool schemas, guardrail pipeline, budget config, tracing, and tests. Use this whenever the user wants to start, bootstrap, scaffold, or set up a new AI agent, add an agent to an existing system, or prototype one to validate tool design — including open-ended asks like "help me build an agent that does X".
---

# Agent Scaffold

Generate a complete agent project: the ReAct loop, tool schemas, a six-layer
guardrail pipeline, budget enforcement, retry and fallback, tracing, and a test
suite that runs without an API key.

This skill ships a working generator. Run it rather than writing the structure
out by hand.

## When to Use

- Starting a new agent project from scratch.
- Adding an agent to an existing system.
- Prototyping to validate tool design before committing to an implementation.

## Generate the project

```bash
python scripts/scaffold.py \
  --name analytics_agent \
  --out ./analytics_agent \
  --tools run_sql,create_chart \
  --description "answers business questions over the analytics warehouse"
```

Then confirm it works before changing anything:

```bash
cd analytics_agent && pip install -e '.[dev]' && pytest
```

The generated suite drives the real agent loop against a fake model, so it
passes offline with no key. If it does not pass, stop and fix that first.

### Options

| Flag | Default | Notes |
|---|---|---|
| `--name` | required | snake_case identifier for the agent |
| `--out` | required | output directory |
| `--tools` | required | comma-separated `verb_noun` names, 1-7 of them |
| `--description` | generic | one line, used in the system prompt and README |
| `--level` | `3` | architecture level 0-5 |
| `--model` | `claude-sonnet-5` | primary model |
| `--fallback-model` | `claude-haiku-4-5` | second model in the fallback chain |
| `--dry-run` | off | list the files without writing them |
| `--force` | off | overwrite a non-empty directory |

The generator refuses more than 7 tools and warns when a tool name is not
`verb_noun`, when level 4+ is requested without a permission split, and when
tools are requested at a level that has no dynamic tool selection.

## Choosing the level before you generate

Pass `--level` deliberately. Auto-defaulting to 3 is right for most agents but
wrong for the two ends:

- No tools needed, single turn → **L0**. Do not scaffold an agent; make one call.
- Fixed, predictable sequence → **L1/L2**. A chain or router, not a loop.
- Dynamic tool selection → **L3**. The default.
- Genuinely different permissions or models per step → **L4**. Needs justification.
- Open-ended exploration → **L5**. Rare, and expensive to get right.

## What gets generated

```
{name}/
├── main.py              # Entrypoint: wires tools, prints answer + cost
├── agent.py             # ReAct loop: budgets, guardrails, degradation
├── config.py            # AgentConfig — every limit, checked before each call
├── models.py            # AgentRun, AgentStep, ToolResult, Usage
├── reliability.py       # Backoff with jitter, circuit breaker, fallback chain
├── tracing.py           # One structured event per step
├── tools/
│   ├── __init__.py      # BaseTool contract + registry with the 7-tool ceiling
│   └── {tool}.py        # One per --tools entry, constrained schema, stub body
├── guardrails/
│   ├── input.py         # Layers 1, 2, 4: schema, injection, semantic intent
│   ├── output.py        # Layer 6: PII, prompt-leak, grounding
│   └── tool_guards.py   # Layer 5: read-only SQL, path confinement, sandbox
├── tests/
│   ├── conftest.py      # Fake Anthropic client and tools
│   ├── test_tools.py    # Registry and BaseTool contract
│   ├── test_guardrails.py
│   ├── test_agent.py    # Loop integration against the fake model
│   └── evals/golden.yaml
└── pyproject.toml
```

Templates live in `assets/`. Read one there rather than guessing at what the
generator emits.

## What the generated loop already enforces

1. Budgets checked **before** every model call — iterations, tool calls, cost,
   tokens, and wall clock. A limit you discover after the fact is a bill.
2. Tool arguments validated against a constrained schema; failures return a
   tool error the model can recover from, not an exception.
3. Tool output truncated at 10,000 chars before it re-enters the context.
4. All parallel tool results returned in a **single** user turn. Splitting them
   trains the model to stop making parallel calls.
5. Retry with jittered backoff, a per-provider circuit breaker, and a model
   fallback chain that skips open circuits.
6. Graceful degradation: full agent → no tools → honest apology. Never a
   silent failure.
7. Adaptive thinking plus `effort`, never a fixed `budget_tokens` — current
   models reject that outright.

## After generating

The scaffold is a skeleton with correct bones, not a finished agent. In order:

1. **Implement `execute` in each tool.** They return stubs.
2. **Rewrite each tool's `description`.** The model selects tools from these,
   so the TODO placeholders are the single biggest source of wrong-tool bugs.
   State when to use it, when not to, what it returns, and its limits.
3. **Fill in `tests/evals/golden.yaml`** with real questions and expected tools.
4. **Point `tracing.py` at Langfuse or LangSmith** instead of the logging sink.
5. **Set alerts** on error rate, cost per hour, P95 latency, and provider outage.

Then run `/agentic-design-review` against the result before shipping it.

## Extending the templates

To change what every future agent gets, edit `assets/` — not the generated
output. Templates use `string.Template` syntax (`${name}`), so a literal dollar
sign must be written `$$`. After editing, regenerate and run the generated test
suite; that is what catches a broken template.
