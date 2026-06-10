#!/bin/bash
# promise-checker.sh — Stop hook
#
# Fires when Claude finishes a response. Scans the last assistant turn for
# "performative compliance" phrases — cases where Claude says it saved, noted,
# or remembered something without actually calling a write tool.
#
# Adapted from flonat/claude-research (github.com/flonat/claude-research).
#
# Install: add to .claude/settings.json under "Stop":
#   "Stop": [{
#     "hooks": [{"type": "command", "command": "bash .claude/hooks/promise-checker.sh"}]
#   }]

set -euo pipefail

# Phrases that indicate Claude claims to have persisted something.
PROMISE_PATTERNS=(
  "I'll remember"
  "I've noted"
  "I've saved"
  "I've recorded"
  "I'll note"
  "I've logged"
  "noted that"
  "I'll keep that in mind"
  "I've updated"
  "I've added that"
  "saved to memory"
  "I've made a note"
)

# Read Claude Code hook input from stdin (JSON).
INPUT=$(cat)

# Extract the last assistant message text.
LAST_TURN=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
messages = data.get('messages', [])
for msg in reversed(messages):
    if msg.get('role') == 'assistant':
        content = msg.get('content', '')
        if isinstance(content, list):
            text = ' '.join(b.get('text','') for b in content if isinstance(b,dict))
        else:
            text = str(content)
        print(text)
        break
" 2>/dev/null || echo "")

if [ -z "$LAST_TURN" ]; then
  exit 0
fi

# Check whether any write tools were called in this turn.
WROTE_FILE=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
tool_uses = [m for m in data.get('messages', []) if m.get('role') == 'tool_use']
write_tools = {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}
found = any(t.get('name','') in write_tools for t in tool_uses)
print('yes' if found else 'no')
" 2>/dev/null || echo "no")

# Scan for promise phrases.
FOUND_PROMISE=""
for pattern in "${PROMISE_PATTERNS[@]}"; do
  if echo "$LAST_TURN" | grep -qi "$pattern"; then
    FOUND_PROMISE="$pattern"
    break
  fi
done

if [ -n "$FOUND_PROMISE" ] && [ "$WROTE_FILE" = "no" ]; then
  # Emit feedback to Claude via hookSpecificOutput.
  python3 -c "
import json
feedback = {
  'hookSpecificOutput': {
    'hookEventName': 'Stop',
    'permissionDecision': 'allow',
    'additionalContext': (
        'promise-checker: You said something like \"{phrase}\" but no file was written. '
        'If you intended to save or record something, do it now with a Write or Edit call. '
        'If you only meant it conversationally, that is fine — but be precise: '
        'do not say you have saved something you have not saved.'
    ).format(phrase='$FOUND_PROMISE')
  }
}
print(json.dumps(feedback))
"
fi

exit 0
