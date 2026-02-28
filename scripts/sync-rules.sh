#!/usr/bin/env bash
# sync-rules.sh — Generate tool-specific rule files from AGENTS.md
# Usage: ./scripts/sync-rules.sh          # Write all targets
#        ./scripts/sync-rules.sh --check   # Diff-only mode (exit 1 if out of sync)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CANONICAL="$PKG_DIR/AGENTS.md"

# Generated files go to the consuming project root, not the package subdirectory.
# If the package lives at <repo>/agentic-ai-skills/, outputs land at <repo>/.
# If the package IS the repo root, outputs stay at root.
PROJECT_ROOT="$(cd "$PKG_DIR/.." && pwd)"
if [ ! -d "$PROJECT_ROOT/.git" ] && [ -d "$PKG_DIR/.git" ]; then
  PROJECT_ROOT="$PKG_DIR"
fi

if [ ! -f "$CANONICAL" ]; then
  echo "ERROR: $CANONICAL not found" >&2
  exit 1
fi

MODE="write"
if [ "${1:-}" = "--check" ]; then
  MODE="check"
fi

CANONICAL_CONTENT="$(cat "$CANONICAL")"
ERRORS=0

# Generate a target file with a header prepended to canonical content.
# Args: $1=target_path $2=header_text
generate() {
  local target="$1"
  local header="$2"
  local expected
  expected="$(printf '%s\n\n%s\n' "$header" "$CANONICAL_CONTENT")"

  if [ "$MODE" = "check" ]; then
    if [ ! -f "$target" ]; then
      echo "MISSING: $target" >&2
      ERRORS=$((ERRORS + 1))
      return
    fi
    if ! diff -q <(printf '%s\n' "$expected") "$target" >/dev/null 2>&1; then
      echo "OUT OF SYNC: $target" >&2
      diff --unified=3 <(printf '%s\n' "$expected") "$target" >&2 || true
      ERRORS=$((ERRORS + 1))
    else
      echo "OK: $target"
    fi
  else
    mkdir -p "$(dirname "$target")"
    printf '%s\n' "$expected" > "$target"
    echo "WROTE: $target"
  fi
}

# --- Target 1: .cursor/rules/agentic-ai.mdc ---
CURSOR_HEADER="---
description: Agentic AI production rules
alwaysApply: true
---"
generate "$PROJECT_ROOT/.cursor/rules/agentic-ai.mdc" "$CURSOR_HEADER"

# --- Target 2: .github/copilot-instructions.md ---
COPILOT_HEADER="<!-- GitHub Copilot Instructions — auto-generated from AGENTS.md -->
<!-- Do not edit directly. Run scripts/sync-rules.sh to regenerate. -->"
generate "$PROJECT_ROOT/.github/copilot-instructions.md" "$COPILOT_HEADER"

# --- Target 3: .windsurfrules ---
WINDSURF_HEADER="# Windsurf Rules — auto-generated from AGENTS.md
# Do not edit directly. Run scripts/sync-rules.sh to regenerate."
generate "$PROJECT_ROOT/.windsurfrules" "$WINDSURF_HEADER"

# --- Target 4: .codex/AGENTS.md ---
CODEX_HEADER="<!-- Auto-generated from AGENTS.md — do not edit directly. -->
<!-- Run scripts/sync-rules.sh to regenerate. -->"
generate "$PROJECT_ROOT/.codex/AGENTS.md" "$CODEX_HEADER"

if [ "$MODE" = "check" ]; then
  if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "FAIL: $ERRORS file(s) out of sync. Run scripts/sync-rules.sh to fix." >&2
    exit 1
  else
    echo ""
    echo "PASS: All generated files match AGENTS.md."
  fi
fi
