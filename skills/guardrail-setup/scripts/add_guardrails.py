#!/usr/bin/env python3
"""Generate a defence-in-depth guardrail package into an existing project.

    python scripts/add_guardrails.py --out ./myproject/guardrails --sql --pii-heavy

Layers 1, 2, 4 and 6 are always generated. Layer 3 ships as a documented seam
with a NullClassifier. Layer 5 guards are opt-in, because generating a sandbox
checker for a project with no code execution is noise, not safety.

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

# Emitted no matter what: these are the layers every agent needs.
ALWAYS = (
    "__init__.py",
    "schema.py",
    "content_filter.py",
    "semantic.py",
    "classifier.py",
    "output.py",
    "pipeline.py",
    "README.md",
    "tool_guards/__init__.py",
    "tool_guards/base.py",
    "tests/__init__.py",
    "tests/test_input.py",
    "tests/test_output.py",
)

# Opt-in layer 5 guards. Each contributes a module, its re-exports, and tests.
GUARDS: dict[str, dict[str, object]] = {
    "sql": {
        "flag": "--sql",
        "module": "sql",
        "exports": ["enforce_limit", "validate_sql"],
        "files": ("tool_guards/sql.py", "tests/test_sql.py"),
        "why": "any tool that issues SQL",
    },
    "files": {
        "flag": "--files",
        "module": "paths",
        "exports": ["validate_path", "validate_write_path"],
        "files": ("tool_guards/paths.py", "tests/test_paths.py"),
        "why": "any tool that reads or writes files",
    },
    "code_exec": {
        "flag": "--code-exec",
        "module": "sandbox",
        "exports": ["SANDBOX_SPEC", "assert_sandboxed", "docker_run_args"],
        "files": ("tool_guards/sandbox.py", "tests/test_sandbox.py"),
        "why": "any tool that executes model-supplied code",
    },
}


class GeneratorError(SystemExit):
    def __init__(self, message: str) -> None:
        super().__init__(f"error: {message}")


def build_context(package: str, max_query_chars: int, selected: list[str]) -> dict[str, str]:
    imports: list[str] = []
    exports: list[str] = []
    for key in selected:
        guard = GUARDS[key]
        names = sorted(guard["exports"])  # type: ignore[arg-type]
        imports.append(f"from .{guard['module']} import {', '.join(names)}")
        exports.extend(f'    "{name}",' for name in names)
    return {
        "package": package,
        "max_query_chars": str(max_query_chars),
        "tool_guard_imports": "\n".join(imports),
        "tool_guard_exports": ("\n".join(sorted(exports)) + "\n") if exports else "",
    }


def render(text: str, context: dict[str, str], source: str) -> str:
    out = Template(text).safe_substitute(context)
    if leftover := LEFTOVER_TOKEN.findall(out):
        print(
            f"warning: {source} has unresolved placeholders: {sorted(set(leftover))}",
            file=sys.stderr,
        )
    return out


def plan(selected: list[str]) -> list[str]:
    """Relative output paths to generate, in a stable order."""
    files = list(ALWAYS)
    for key in selected:
        files.extend(GUARDS[key]["files"])  # type: ignore[arg-type]
    return sorted(set(files))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a guardrail package into an existing project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Layer 5 guards are opt-in. Pass the flag matching each risk your agent "
        "actually carries:\n"
        + "\n".join(f"  {g['flag']:<14} {g['why']}" for g in GUARDS.values()),
    )
    parser.add_argument(
        "--out", required=True, type=Path, help="target package directory"
    )
    parser.add_argument(
        "--package",
        default=None,
        help="importable package name (defaults to the --out directory name)",
    )
    parser.add_argument("--sql", action="store_true", help="read-only SQL enforcement")
    parser.add_argument("--files", action="store_true", help="path confinement")
    parser.add_argument(
        "--code-exec", action="store_true", help="code execution sandbox spec"
    )
    parser.add_argument(
        "--all-guards", action="store_true", help="enable every layer 5 guard"
    )
    parser.add_argument(
        "--max-query-chars",
        type=int,
        default=5000,
        help="layer 1 input length ceiling (default: 5000)",
    )
    parser.add_argument("--dry-run", action="store_true", help="list files only")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args(argv)

    package = args.package or args.out.name
    if not IDENTIFIER.match(package):
        raise GeneratorError(
            f"package name {package!r} must be snake_case. Pass --package to override "
            "the directory name."
        )
    if args.max_query_chars < 1:
        raise GeneratorError("--max-query-chars must be positive")

    selected = [k for k in GUARDS if args.all_guards or getattr(args, k)]
    files = plan(selected)

    if args.out.exists() and any(args.out.iterdir()) and not (args.force or args.dry_run):
        raise GeneratorError(f"{args.out} is not empty; pass --force to overwrite")

    context = build_context(package, args.max_query_chars, selected)

    for rel in files:
        source = ASSETS / f"{rel}.tmpl"
        if not source.is_file():
            raise GeneratorError(f"missing template: {source}")
        destination = args.out / rel
        if args.dry_run:
            print(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            render(source.read_text(encoding="utf-8"), context, rel), encoding="utf-8"
        )

    if args.dry_run:
        print(f"\n{len(files)} files would be written to {args.out}")
        return 0

    print(f"Generated {package} ({len(files)} files) in {args.out}")
    if selected:
        print(f"  layer 5 guards: {', '.join(sorted(selected))}")
    else:
        print("  layer 5 guards: none selected")
        print(
            "  note: no tool guards were generated. If any tool issues SQL, touches "
            "the filesystem, or runs model-supplied code, re-run with the matching "
            "flag — those are the highest-value guards in most agents."
        )

    print("\nNext:")
    print(f"  pytest {args.out}")
    print(f"  then wire GuardrailPipeline into your request path (see {args.out}/README.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
