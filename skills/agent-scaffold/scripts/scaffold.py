#!/usr/bin/env python3
"""Generate a production-ready agent project from the bundled templates.

    python scripts/scaffold.py --name analytics_agent --out ./analytics_agent \\
        --tools run_sql,create_chart \\
        --description "answers business questions over the analytics warehouse"

Everything it emits compiles and its test suite passes with no API key, so you
can run `pytest` in the generated project immediately and start replacing stubs.

`--level` changes the code that comes out, not just the docstrings:

    0, 1  refused. These are not agents; see the message the generator prints.
    2     a router: one classification, one handler, two model calls, no loop.
    3+    a ReAct loop with dynamic tool selection.

Standard library only, so it runs anywhere Python 3.12 does.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from string import Template

ASSETS = Path(__file__).resolve().parent.parent / "assets"

IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*\Z")
LEFTOVER_TOKEN = re.compile(r"\$\{[a-z_][a-z0-9_]*\}")

# Mirrors MAX_TOOLS_PER_AGENT in the generated tools package.
MAX_TOOLS = 7

# Emitted at every supported level.
ALWAYS = (
    "config.py",
    "models.py",
    "reliability.py",
    "llm.py",
    "tracing.py",
    "main.py",
    "pyproject.toml",
    "README.md",
    "guardrails/__init__.py",
    "guardrails/input.py",
    "guardrails/output.py",
    "guardrails/tool_guards.py",
    "tools/__init__.py",
    "tests/conftest.py",
    "tests/test_tools.py",
    "tests/test_guardrails.py",
    "tests/evals/golden.yaml",
)

# (template, destination) pairs chosen by architecture level. Both loop shapes
# expose the same `Agent` class, so the destination filename is identical and
# swapping levels does not change any call site.
LOOPS: dict[str, tuple[tuple[str, str], ...]] = {
    "router": (
        ("agent_router.py", "agent.py"),
        ("tests/test_agent_router.py", "tests/test_agent.py"),
    ),
    "react": (
        ("agent.py", "agent.py"),
        ("tests/test_agent.py", "tests/test_agent.py"),
    ),
}

REFUSAL = {
    0: (
        "level 0 is a single model call, not an agent. Wrapping a loop around one "
        "call adds cost, latency, and failure modes for nothing.\n"
        "  Write the call directly, and set max_tokens and a timeout on it."
    ),
    1: (
        "level 1 is a prompt chain: a fixed sequence you write out, not a loop that "
        "decides what to do next.\n"
        "  Write the steps directly. If the sequence needs to branch on a result, "
        "you want --level 2 (router); if it needs to choose tools dynamically, "
        "--level 3."
    ),
}


class ScaffoldError(SystemExit):
    def __init__(self, message: str) -> None:
        super().__init__(f"error: {message}")


def pascal(snake: str) -> str:
    """run_sql -> RunSql"""
    return "".join(part.capitalize() for part in snake.split("_") if part)


def loop_kind(level: int) -> str:
    return "router" if level == 2 else "react"


def tool_template(tool: str) -> str:
    """Pick the closest-fitting tool template for a tool name.

    A tool called `run_sql` should not be handed a free-text `query: str` — that
    contradicts the constrained-parameter rule the rest of this package
    enforces. Add further shapes here as you find yourself writing the same
    schema twice.
    """
    return "tools/_tool_sql.py" if "sql" in tool.split("_") else "tools/_tool.py"


def validate(name: str, tools: list[str], level: int) -> None:
    if not IDENTIFIER.match(name):
        raise ScaffoldError(
            f"--name {name!r} must be snake_case: lowercase, digits, underscores"
        )
    if not 0 <= level <= 5:
        raise ScaffoldError("--level must be between 0 and 5")
    if level in REFUSAL:
        raise ScaffoldError(
            f"{REFUSAL[level]}\n"
            "  Re-run with --level 2 or --level 3 if you do need an agent."
        )
    if not tools:
        raise ScaffoldError("--tools needs at least one tool name")
    if len(tools) > MAX_TOOLS:
        raise ScaffoldError(
            f"{len(tools)} tools exceeds the {MAX_TOOLS}-tool limit. Split the agent, "
            "or enable tool search, rather than raising the ceiling."
        )
    if len(set(tools)) != len(tools):
        raise ScaffoldError(f"duplicate tool names: {tools}")
    for tool in tools:
        if not IDENTIFIER.match(tool):
            raise ScaffoldError(f"tool {tool!r} must be snake_case")


def advisories(tools: list[str], level: int) -> list[str]:
    """Design warnings worth surfacing that should not block generation."""
    notes: list[str] = []
    for tool in tools:
        if "_" not in tool:
            notes.append(
                f"tool {tool!r} is not verb_noun (e.g. run_sql, create_chart); "
                "vague names hurt tool selection"
            )
    if level == 2 and len(tools) == 1:
        notes.append(
            "a router with one handler is just a function call. Either add the "
            "other task types, or drop to a direct call."
        )
    if level >= 4:
        notes.append(
            f"level {level} is a composition of level-3 agents. This generated one "
            "agent; run the generator again per agent, and give each only the tools "
            "its permission level allows."
        )
    return notes


def build_context(args: argparse.Namespace, tools: list[str]) -> dict[str, str]:
    imports = "\n".join(f"from tools.{t} import {pascal(t)}" for t in tools)
    instances = ", ".join(f"{pascal(t)}()" for t in tools)
    return {
        "agent_name": args.name,
        "agent_class": pascal(args.name),
        "description": args.description,
        "level": str(args.level),
        "model": args.model,
        "fallback_model": args.fallback_model,
        "tool_imports": imports,
        "tool_instances": instances,
        "first_tool": tools[0],
    }


def render(text: str, context: dict[str, str], source: str) -> str:
    out = Template(text).safe_substitute(context)
    if leftover := LEFTOVER_TOKEN.findall(out):
        print(
            f"warning: {source} has unresolved placeholders: {sorted(set(leftover))}",
            file=sys.stderr,
        )
    return out


def plan(tools: list[str], level: int) -> list[tuple[str, str, str | None]]:
    """(template path, output path, tool name) triples, in a stable order."""
    jobs: list[tuple[str, str, str | None]] = [(f, f, None) for f in ALWAYS]
    jobs.extend((src, dst, None) for src, dst in LOOPS[loop_kind(level)])
    jobs.extend((tool_template(t), f"tools/{t}.py", t) for t in tools)
    return sorted(jobs, key=lambda job: job[1])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a production-ready agent project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--name", required=True, help="agent name, snake_case")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument(
        "--tools",
        required=True,
        help="comma-separated verb_noun tool names, e.g. run_sql,create_chart",
    )
    parser.add_argument(
        "--description",
        default="an agent scaffolded by agentic-ai-skills.",
        help="one line, used in the system prompt and README",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=3,
        help="architecture level: 2 for a router, 3+ for a ReAct loop (0 and 1 are refused)",
    )
    parser.add_argument("--model", default="claude-sonnet-5", help="primary model")
    parser.add_argument(
        "--fallback-model", default="claude-haiku-4-5", help="fallback model"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="list files without writing them"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite a non-empty directory"
    )
    args = parser.parse_args(argv)

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    validate(args.name, tools, args.level)

    out_root: Path = args.out
    if out_root.exists() and any(out_root.iterdir()) and not (args.force or args.dry_run):
        raise ScaffoldError(f"{out_root} is not empty; pass --force to overwrite")

    context = build_context(args, tools)
    jobs = plan(tools, args.level)
    kind = loop_kind(args.level)

    for template_rel, out_rel, tool in jobs:
        source = ASSETS / f"{template_rel}.tmpl"
        if not source.is_file():
            raise ScaffoldError(f"missing template: {source}")
        destination = out_root / out_rel
        if args.dry_run:
            print(destination)
            continue
        local = dict(context)
        if tool is not None:
            local["tool_name"] = tool
            local["tool_class"] = pascal(tool)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            render(source.read_text(encoding="utf-8"), local, template_rel),
            encoding="utf-8",
        )

    if args.dry_run:
        print(f"\n{len(jobs)} files would be written to {out_root} ({kind} loop)")
        return 0

    shape = "router: two model calls, one handler, no loop" if kind == "router" else "ReAct loop"
    print(f"Scaffolded {args.name} ({len(jobs)} files) in {out_root}")
    print(f"  level {args.level} -> {shape}")
    sql_tools = [t for t in tools if tool_template(t).endswith("_tool_sql.py")]
    if sql_tools:
        print(f"  SQL-shaped tools: {', '.join(sql_tools)} (read-only guard wired in)")
    for note in advisories(tools, args.level):
        print(f"  note: {note}")
    print("\nNext:")
    print(f"  cd {out_root} && pip install -e '.[dev]' && pytest")
    print(f"  then implement execute() in {out_root}/tools/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
