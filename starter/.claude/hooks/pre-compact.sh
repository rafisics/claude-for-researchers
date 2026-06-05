#!/usr/bin/env bash
# pre-compact.sh
#
# Runs automatically before Claude compresses the conversation context.
# Claude Code fires this hook when the context window is nearly full.
#
# PURPOSE: Ensure you don't lose track of where you are when the context
# rolls over. After compaction, Claude starts a summarised version of the
# conversation — this hook writes a timestamp marker so you can see exactly
# when a compaction happened and resume cleanly.
#
# HOW IT WORKS:
# Claude Code passes a JSON payload on stdin. We read it but in practice
# the useful work here is file-level: stamp CLAUDE.md and optionally
# snapshot next-session-prompts.md.
#
# SETUP: Make sure settings.json references this file:
#   "PreCompact": [{ "hooks": [{ "type": "command", "command": "bash .claude/hooks/pre-compact.sh" }] }]

set -euo pipefail

# Read stdin (Claude passes JSON context here; we don't need it but must consume it)
read -r -t 2 INPUT || INPUT=""

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

# --- 1. Stamp CLAUDE.md ---
# Appends a visible marker so you know a compaction occurred.
# Claude is instructed in CLAUDE.md to prune these when they accumulate.
if [[ -f "CLAUDE.md" ]]; then
    cat >> CLAUDE.md << MARKER

## ⚠️ Auto-saved before context compact [$TIMESTAMP]
Session was compacted. Last known state is in the "Current status" section above.
To resume: start new session, open next-session-prompts.md, paste the top prompt.
MARKER
fi

# --- 2. Snapshot next-session-prompts.md (optional) ---
# Creates a timestamped backup so you never lose the task log.
# Remove this block if you don't want backup files.
if [[ -f "next-session-prompts.md" ]]; then
    BACKUP_DIR=".claude/snapshots"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/next-session-prompts-$(date +%Y%m%d-%H%M).md"
    cp "next-session-prompts.md" "$BACKUP_FILE"
fi

# --- 3. Optional: git commit current state ---
# Uncomment this block to auto-commit before compaction.
# Useful if you run long sessions and want a breadcrumb.
#
# if git diff --quiet && git diff --cached --quiet; then
#     : # nothing to commit
# else
#     git add CLAUDE.md next-session-prompts.md 2>/dev/null || true
#     git commit -m "Auto-save before context compact [$TIMESTAMP]" \
#         --no-verify 2>/dev/null || true
# fi

exit 0
