#!/usr/bin/env bash
# validate.sh — Pre-publish checks for the agentic-ai-skills package.
# Exit 0 = all checks pass. Exit 1 = issues found.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ERRORS=0
WARNINGS=0

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; ERRORS=$((ERRORS + 1)); }
warn() { echo "  WARN: $1"; WARNINGS=$((WARNINGS + 1)); }

echo "=== Agentic AI Skills — Validation ==="
echo ""

# --- Check 1: AGENTS.md line count ≤ 180 ---
echo "[1/5] AGENTS.md line count"
AGENTS_LINES="$(wc -l < "$ROOT_DIR/AGENTS.md" | tr -d ' ')"
if [ "$AGENTS_LINES" -le 180 ]; then
  pass "AGENTS.md is $AGENTS_LINES lines (limit: 180)"
else
  fail "AGENTS.md is $AGENTS_LINES lines (limit: 180)"
fi

# --- Check 2: SKILL.md line counts ≤ 500 ---
echo "[2/5] SKILL.md line counts"
while IFS= read -r skill_file; do
  SKILL_LINES="$(wc -l < "$skill_file" | tr -d ' ')"
  SKILL_NAME="$(basename "$(dirname "$skill_file")")"
  if [ "$SKILL_LINES" -le 500 ]; then
    pass "$SKILL_NAME/SKILL.md is $SKILL_LINES lines (limit: 500)"
  else
    fail "$SKILL_NAME/SKILL.md is $SKILL_LINES lines (limit: 500)"
  fi
done < <(find "$ROOT_DIR/skills" -name "SKILL.md" -type f 2>/dev/null)

# --- Check 3: SKILL.md frontmatter has name and description ---
echo "[3/5] SKILL.md frontmatter validation"
while IFS= read -r skill_file; do
  SKILL_NAME="$(basename "$(dirname "$skill_file")")"
  # Extract YAML frontmatter between --- delimiters
  FRONTMATTER="$(sed -n '/^---$/,/^---$/p' "$skill_file" | head -20)"
  if echo "$FRONTMATTER" | grep -q "^name:"; then
    if echo "$FRONTMATTER" | grep -q "^description:"; then
      pass "$SKILL_NAME/SKILL.md has name and description"
    else
      fail "$SKILL_NAME/SKILL.md missing 'description' in frontmatter"
    fi
  else
    fail "$SKILL_NAME/SKILL.md missing 'name' in frontmatter"
  fi
done < <(find "$ROOT_DIR/skills" -name "SKILL.md" -type f 2>/dev/null)

# --- Check 4: No local paths in tracked files ---
echo "[4/5] No local paths"
LOCAL_PATH_REGEX='(/Users/|/home/|C:\\)'
FOUND_PATHS=0
while IFS= read -r file; do
  # Skip validation scripts, sync scripts, and README (which documents the regex)
  case "$file" in
    "$ROOT_DIR/validate.sh"|"$ROOT_DIR/scripts/"*|"$ROOT_DIR/README.md") continue ;;
  esac
  if grep -qE "$LOCAL_PATH_REGEX" "$file" 2>/dev/null; then
    fail "Local path found in $(basename "$file"): $(grep -nE "$LOCAL_PATH_REGEX" "$file" | head -1)"
    FOUND_PATHS=1
  fi
done < <(find "$ROOT_DIR" -type f \( -name "*.md" -o -name "*.mdc" -o -name "*.sh" -o -name "*.yaml" -o -name "*.yml" \) ! -path "*/.git/*" 2>/dev/null)
if [ "$FOUND_PATHS" -eq 0 ]; then
  pass "No local paths found in any tracked file"
fi

# --- Check 5: Generated files match canonical source ---
echo "[5/5] Generated file parity"
# Use the sync script's --check mode
if bash "$ROOT_DIR/scripts/sync-rules.sh" --check >/dev/null 2>&1; then
  pass "All generated files match AGENTS.md"
else
  fail "Generated files out of sync — run scripts/sync-rules.sh"
fi

# --- Summary ---
echo ""
echo "=== Results ==="
TOTAL=$((ERRORS + WARNINGS))
if [ "$ERRORS" -eq 0 ]; then
  echo "ALL CHECKS PASSED ($WARNINGS warning(s))"
  exit 0
else
  echo "FAILED: $ERRORS error(s), $WARNINGS warning(s)"
  exit 1
fi
