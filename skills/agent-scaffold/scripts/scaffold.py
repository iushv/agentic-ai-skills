#!/usr/bin/env python3
"""Generate a production-ready agent project from the bundled templates.

    python scripts/scaffold.py --name analytics_agent --out ./analytics_agent \\
        --tools run_sql,create_chart \\
        --description "answers business questions over the analytics warehouse"

Everything it emits compiles and its test suite passes with no API key, so you
can run `pytest` in the generated project immediately and start replacing stubs.

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

# The per-tool template is expanded once for each requested tool rather than
# copied verbatim like everything else.
PER_TOOL_TEMPLATE = "_tool.py"


class ScaffoldError(SystemExit):
    def __init__(self, message: str) -> None:
        super().__init__(f"error: {message}")


def pascal(snake: str) -> str:
    """run_sql -> RunSql"""
    return "".join(part.capitalize() for part in snake.split("_") if part)


def validate(name: str, tools: list[str], level: int) -> None:
    if not IDENTIFIER.match(name):
        raise ScaffoldError(
            f"--name {name!r} must be snake_case: lowercase, digits, underscores"
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
    if not 0 <= level <= 5:
        raise ScaffoldError("--level must be between 0 and 5")


def advisories(tools: list[str], level: int) -> list[str]:
    """Design warnings that are worth surfacing but should not block generation."""
    notes: list[str] = []
    for tool in tools:
        if "_" not in tool:
            notes.append(
                f"tool {tool!r} is not verb_noun (e.g. run_sql, create_chart); "
                "vague names hurt tool selection"
            )
    if level >= 4:
        notes.append(
            "level 4+ is only justified when agents need different permissions or "
            "models. If they do not, collapse this to a single level-3 agent."
        )
    if level <= 1 and tools:
        notes.append(
            f"level {level} means no dynamic tool selection, but {len(tools)} tool(s) "
            "were requested. Consider --level 3, or drop the tools."
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


def render(text: str, context: dict[str, str], source: Path) -> str:
    out = Template(text).safe_substitute(context)
    if leftover := LEFTOVER_TOKEN.findall(out):
        print(
            f"warning: {source.name} has unresolved placeholders: {sorted(set(leftover))}",
            file=sys.stderr,
        )
    return out


def plan(tools: list[str]) -> list[tuple[Path, Path, str | None]]:
    """Return (source template, relative output path, tool name) triples."""
    if not ASSETS.is_dir():
        raise ScaffoldError(f"assets directory not found at {ASSETS}")
    jobs: list[tuple[Path, Path, str | None]] = []
    for template in sorted(ASSETS.rglob("*.tmpl")):
        rel = template.relative_to(ASSETS)
        out_rel = rel.with_suffix("")  # drop .tmpl
        if out_rel.name == PER_TOOL_TEMPLATE:
            for tool in tools:
                jobs.append((template, out_rel.with_name(f"{tool}.py"), tool))
        else:
            jobs.append((template, out_rel, None))
    return jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a production-ready agent project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="one-line description used in the system prompt and README",
    )
    parser.add_argument("--level", type=int, default=3, help="architecture level 0-5")
    parser.add_argument("--model", default="claude-sonnet-5", help="primary model")
    parser.add_argument(
        "--fallback-model", default="claude-haiku-4-5", help="fallback model"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="list files without writing them"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing directory"
    )
    args = parser.parse_args(argv)

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    validate(args.name, tools, args.level)

    out_root: Path = args.out
    if out_root.exists() and any(out_root.iterdir()) and not (args.force or args.dry_run):
        raise ScaffoldError(f"{out_root} is not empty; pass --force to overwrite")

    context = build_context(args, tools)
    jobs = plan(tools)

    for template, out_rel, tool in jobs:
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
            render(template.read_text(encoding="utf-8"), local, template),
            encoding="utf-8",
        )

    if args.dry_run:
        print(f"\n{len(jobs)} files would be written to {out_root}")
        return 0

    print(f"Scaffolded {args.name} ({len(jobs)} files) in {out_root}")
    for note in advisories(tools, args.level):
        print(f"  note: {note}")
    print("\nNext:")
    print(f"  cd {out_root} && pip install -e '.[dev]' && pytest")
    print(f"  then implement execute() in {out_root}/tools/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
