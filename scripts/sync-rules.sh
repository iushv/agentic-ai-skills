#!/usr/bin/env bash
# sync-rules.sh — Generate tool-specific rule files and skill mirrors from AGENTS.md
# Usage: ./scripts/sync-rules.sh                       # All targets (default)
#        ./scripts/sync-rules.sh --check               # Diff-only mode (exit 1 if out of sync)
#        ./scripts/sync-rules.sh --tools claude         # Only Claude Code mirrors
#        ./scripts/sync-rules.sh --tools cursor,codex   # Comma-separated subset
#        ./scripts/sync-rules.sh --clean-stale          # Remove old generated files with markers
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CANONICAL="$PKG_DIR/AGENTS.md"
MARKER="agentic-ai-skills:auto-generated"

# Root detection: prefer git rev-parse for monorepo/worktree correctness.
# If git root equals the package dir (package is its own repo), use parent instead.
PROJECT_ROOT="$(git -C "$PKG_DIR" rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -z "$PROJECT_ROOT" ] || [ "$PROJECT_ROOT" = "$PKG_DIR" ]; then
  PROJECT_ROOT="$(cd "$PKG_DIR/.." && pwd)"
fi

if [ ! -f "$CANONICAL" ]; then
  echo "ERROR: $CANONICAL not found" >&2
  exit 1
fi

# --- Parse CLI flags ---
MODE="write"
TOOLS="all"
CLEAN_STALE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --check)      MODE="check"; shift ;;
    --tools)      TOOLS="$2"; shift 2 ;;
    --clean-stale) CLEAN_STALE=1; shift ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

# Normalize comma-separated tools into a space-separated set for matching
tool_enabled() {
  [ "$TOOLS" = "all" ] && return 0
  echo ",$TOOLS," | grep -q ",$1,"
}

CANONICAL_CONTENT="$(cat "$CANONICAL")"
ERRORS=0

# --- Stale cleanup mode ---
if [ "$CLEAN_STALE" -eq 1 ]; then
  STALE_TARGETS=(
    "$PROJECT_ROOT/.windsurfrules"
    "$PROJECT_ROOT/.github/copilot-instructions.md"
    "$PROJECT_ROOT/.codex/AGENTS.md"
  )
  for target in "${STALE_TARGETS[@]}"; do
    if [ -f "$target" ] && grep -q "$MARKER" "$target" 2>/dev/null; then
      rm "$target"
      echo "REMOVED (stale): $target"
    elif [ -f "$target" ]; then
      echo "SKIPPED (no marker): $target"
    fi
  done
  exit 0
fi

# --- Helper: write or check a generated file ---
generate() {
  local target="$1"
  local content="$2"

  if [ "$MODE" = "check" ]; then
    if [ ! -f "$target" ]; then
      echo "MISSING: $target" >&2
      ERRORS=$((ERRORS + 1))
      return
    fi
    if ! diff -q <(printf '%s\n' "$content") "$target" >/dev/null 2>&1; then
      echo "OUT OF SYNC: $target" >&2
      diff --unified=3 <(printf '%s\n' "$content") "$target" >&2 || true
      ERRORS=$((ERRORS + 1))
    else
      echo "OK: $target"
    fi
  else
    mkdir -p "$(dirname "$target")"
    printf '%s\n' "$content" > "$target"
    echo "WROTE: $target"
  fi
}

# --- Helper: mirror a whole skill directory (byte-identical) ---
# Skills bundle resources alongside SKILL.md (assets/, scripts/, evals/).
# Mirroring only SKILL.md would leave those behind and break the skill's own
# references, so the entire directory is copied.
DIFF_EXCLUDES=(-x '__pycache__' -x '*.pyc' -x '.DS_Store')

mirror_skill_dir() {
  local src_dir="${1%/}"
  local dest_dir="${2%/}"

  if [ "$MODE" = "check" ]; then
    if [ ! -d "$dest_dir" ]; then
      echo "MISSING: $dest_dir" >&2
      ERRORS=$((ERRORS + 1))
      return
    fi
    if ! diff -r "${DIFF_EXCLUDES[@]}" "$src_dir" "$dest_dir" >/dev/null 2>&1; then
      echo "OUT OF SYNC: $dest_dir" >&2
      diff -r "${DIFF_EXCLUDES[@]}" "$src_dir" "$dest_dir" >&2 || true
      ERRORS=$((ERRORS + 1))
    else
      echo "OK: $dest_dir"
    fi
  else
    rm -rf "$dest_dir"
    mkdir -p "$(dirname "$dest_dir")"
    cp -R "$src_dir" "$dest_dir"
    # Never mirror build artefacts.
    find "$dest_dir" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    find "$dest_dir" -name '*.pyc' -delete 2>/dev/null || true
    echo "WROTE: $dest_dir"
  fi
}

# =========================================================================
# Target 1: Cursor — .cursor/rules/agentic-ai.mdc
# =========================================================================
if tool_enabled "cursor"; then
  CURSOR_CONTENT="---
# ${MARKER} — do not edit directly
description: >
  Agentic AI production rules — architecture levels, tool design, safety
  guardrails, reliability, observability, cost control, and testing strategy.
  USE WHEN building, reviewing, or debugging AI agents, tool schemas,
  guardrail pipelines, or multi-agent systems.
alwaysApply: false
---

${CANONICAL_CONTENT}"
  generate "$PROJECT_ROOT/.cursor/rules/agentic-ai.mdc" "$CURSOR_CONTENT"
fi

# =========================================================================
# Target 2: Windsurf — .windsurf/rules/agentic-ai.md
# =========================================================================
if tool_enabled "windsurf"; then
  WINDSURF_CONTENT="---
trigger: model_decision
description: >
  Agentic AI production rules — architecture levels, tool design, safety
  guardrails, reliability, observability, cost control, and testing strategy.
  Use when building, reviewing, or debugging AI agents.
---
<!-- ${MARKER} — do not edit directly -->

${CANONICAL_CONTENT}"
  generate "$PROJECT_ROOT/.windsurf/rules/agentic-ai.md" "$WINDSURF_CONTENT"
fi

# =========================================================================
# Target 3: Copilot — .github/instructions/agentic-ai.instructions.md
# =========================================================================
if tool_enabled "copilot"; then
  COPILOT_CONTENT="---
applyTo: '**/agent*,**/tool*,**/guardrail*,**/react*loop*,**/skills/**'
---
<!-- ${MARKER} — do not edit directly -->

${CANONICAL_CONTENT}"
  generate "$PROJECT_ROOT/.github/instructions/agentic-ai.instructions.md" "$COPILOT_CONTENT"
fi

# =========================================================================
# Target 4: Claude Code skill mirrors — .claude/skills/*/SKILL.md
# =========================================================================
if tool_enabled "claude"; then
  for skill_dir in "$PKG_DIR"/skills/*/; do
    skill_name="$(basename "$skill_dir")"
    if [ -f "$skill_dir/SKILL.md" ]; then
      mirror_skill_dir "$skill_dir" "$PROJECT_ROOT/.claude/skills/$skill_name"
    fi
  done
fi

# =========================================================================
# Target 5: Codex skill mirrors — .agents/skills/*/SKILL.md
# =========================================================================
if tool_enabled "codex"; then
  for skill_dir in "$PKG_DIR"/skills/*/; do
    skill_name="$(basename "$skill_dir")"
    if [ -f "$skill_dir/SKILL.md" ]; then
      mirror_skill_dir "$skill_dir" "$PROJECT_ROOT/.agents/skills/$skill_name"
    fi
  done
fi

# --- Summary ---
if [ "$MODE" = "check" ]; then
  if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "FAIL: $ERRORS file(s) out of sync. Run scripts/sync-rules.sh to fix." >&2
    exit 1
  else
    echo ""
    echo "PASS: All generated files are in sync."
  fi
fi
