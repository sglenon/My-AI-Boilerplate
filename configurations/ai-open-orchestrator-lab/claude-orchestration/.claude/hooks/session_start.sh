#!/usr/bin/env bash
# SessionStart hook — runs reconcile to catch any transcripts parsed while the
# previous session's SessionEnd hook may have been skipped or incomplete.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSER="$HOOK_DIR/../scripts/parse_usage.py"

if [ ! -f "$PARSER" ]; then
    echo "[session_start] parser not found: $PARSER" >&2
    exit 0
fi

# Wrap in || true so transient parse errors don't crash SessionStart
python3 "$PARSER" --reconcile || {
    echo "[session_start] reconcile failed (non-fatal), continuing" >&2
    true
}
