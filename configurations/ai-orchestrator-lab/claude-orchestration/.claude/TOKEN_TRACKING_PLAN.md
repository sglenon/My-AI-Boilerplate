# Token Tracking Implementation Plan

## Overview
Track token usage per-session across all Claude Code sessions in this workspace. Store in `.claude/usage.csv`.

## Decisions Locked

### 1. Data Model
- **Authoritative source:** JSONL transcripts (immutable)
- **CSV role:** Derived projection, re-buildable
- **Tracking level:** Per-session, per-model
- **Dedup:** Mandatory on `message.id` (prevents 2-3x inflation from streaming snapshots)

### 2. CSV Schema (9 columns)
```
Session_ID,Session_Name,Model,Effort,Billable_Tokens,Cache_Tokens,Total_Tokens,Run_ID,Last_Parsed
```

| Column | Source | Immutable | Notes |
|--------|--------|-----------|-------|
| Session_ID | Transcript `sessionId` UUID | Yes | Primary key for upsert |
| Session_Name | `ai-title` record (if renamed) | No | Display name, null if unnamed |
| Model | `message.model` | Yes | e.g., `claude-opus-4-8`, `claude-haiku-4-5-20251001` |
| Effort | Leave blank | N/A | Column reserved, no inference |
| Billable_Tokens | `usage.input_tokens + usage.output_tokens` | Yes | Excludes cache |
| Cache_Tokens | `usage.cache_creation_input_tokens + usage.cache_read_input_tokens` | Yes | Cache-specific |
| Total_Tokens | Billable_Tokens + Cache_Tokens | Yes | Sum of all |
| Run_ID | Full `sessionId` UUID | Yes | Upsert key (same as Session_ID) |
| Last_Parsed | ISO timestamp when parsed | No | Refreshes on reparse |

### 3. Upsert Logic
- **Key:** `(Session_ID, Model)`
- **Behavior:** On reparse, update matching row (refresh costs + Last_Parsed)
- **No Rerun_Of column:** JSONL is audit trail; CSV is current state

### 4. Run_ID Derivation
- **Value:** Full session UUID (same as Session_ID)
- **Why:** Stable across machines, paths, renames. No hashing (preserves uniqueness).

### 5. Session_ID Semantics
- **Immutable:** Always the session UUID from transcript
- **Rename handling:** Session_Name updates, Session_ID stays same
- **Rationale:** Ensures grouping by session doesn't fragment on rename

### 6. Token Math
```
Billable = input_tokens + output_tokens
Cache = cache_creation_input_tokens + cache_read_input_tokens
Total = Billable + Cache
```
- All fields are top-level under `message.usage`, not nested under `iterations[]`
- Missing fields → 0
- Skip `<synthetic>` model records (guard, but unlikely in practice)

### 7. Deduplication
- **Key:** `message.id`
- **Method:** Keep first occurrence, skip duplicates within same transcript
- **Why:** Streaming snapshots create 2-3x duplication; mandatory for correctness

## Implementation Deliverables

### 1. Parser Script
**Path:** `/home/bhong/Projects/aix/claude-orchestration/.claude/scripts/parse_usage.py`

**Modes:**
- `--transcript <path>` — Parse single transcript (SessionEnd hook)
- `--reconcile` — Scan all transcripts newer than CSV mtime, parse missing/changed ones (SessionStart hook)
- `--rebuild` — Wipe CSV and re-parse all transcripts from scratch

**Key logic:**
1. Parse JSONL line by line
2. Dedup on `message.id` (first occurrence wins)
3. Skip malformed lines (try/except per line)
4. Extract: Session_ID (sessionId), Session_Name (ai-title if present), Model, tokens
5. Aggregate by (Session_ID, Model)
6. Upsert into CSV (keyed on Session_ID + Model)
7. Update Last_Parsed timestamp
8. Output to stdout: JSON summary or status

### 2. Hook Wrapper Script
**Path:** `/home/bhong/Projects/aix/claude-orchestration/.claude/hooks/session_end.sh`

**Function:** Read SessionEnd hook JSON from stdin, extract transcript_path, invoke parser

**Signature:**
```bash
#!/bin/bash
# Read JSON from stdin
INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path')
python3 "$(dirname "$0")/../scripts/parse_usage.py" --transcript "$TRANSCRIPT"
```

### 3. Initialize CSV
**Path:** `/home/bhong/Projects/aix/claude-orchestration/.claude/usage.csv`

**Initial content:** Header row only
```
Session_ID,Session_Name,Model,Effort,Billable_Tokens,Cache_Tokens,Total_Tokens,Run_ID,Last_Parsed
```

### 4. Hook Configuration
**File:** `/home/bhong/Projects/aix/claude-orchestration/.claude/settings.json`

**Preserve existing:** `SubagentStart` and `SessionStart` hooks must not be clobbered

**Add:**
```json
{
  "hooks": {
    "SessionEnd": [
      {
        "type": "command",
        "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/session_end.sh"
      }
    ]
  }
}
```

## Critical Correctness Items (MUST implement)

1. **Dedup on `message.id`** — Mandatory. Without it, tokens inflate 2-3x.
2. **Top-level `usage` fields only** — Never sum `iterations[]` (nested structure).
3. **Upsert keyed on (Session_ID, Model)** — Ensures one row per session+model pair.
4. **Immutable Session_ID** — Always UUID; Session_Name for display.
5. **Atomic CSV writes** — Use `os.replace()` to avoid corruption on concurrent hook runs.
6. **Handle missing fields** — `null` → 0 for token fields.
7. **SessionEnd hook stdin is JSON** — Parse with `json.load(sys.stdin)`, extract `transcript_path`.

## Edge Cases

| Case | Handling |
|------|----------|
| Malformed JSONL line | Skip line, log warning, continue |
| Missing `message.usage` | Skip record |
| Missing `message.model` | Skip record |
| Model = `<synthetic>` | Skip (zero tokens anyway) |
| Concurrent SessionEnd hooks | Atomic write prevents corruption; last-write-wins on token values |
| Session renamed mid-life | Session_ID stays UUID; Session_Name updates to new aiTitle |
| Transcript unchanged since last parse | Skip on reconcile if content hash unchanged (optional perf optimization) |
| Crash before SessionEnd hook runs | SessionStart reconciliation catch-up handles it on next startup |

## File Locations

| File | Path | Purpose |
|------|------|---------|
| Parser | `.claude/scripts/parse_usage.py` | Main logic |
| Hook wrapper | `.claude/hooks/session_end.sh` | SessionEnd trigger |
| Output | `.claude/usage.csv` | Token tracking CSV |
| Hook config | `.claude/settings.json` | Register SessionEnd hook |
| Agent defs | `.claude/agents/master.md`, `.claude/agents/worker.md` | Read-only reference (unused in final design) |
| Global settings | `~/.claude/settings.json` | Read-only reference (unused in final design) |
| Transcripts | `~/.claude/projects/-home-bhong-Projects-aix-claude-orchestration/*.jsonl` | Input (immutable) |

## Rebuild & Audit

**Full rebuild (if parsing logic changes):**
```bash
rm .claude/usage.csv
python3 .claude/scripts/parse_usage.py --rebuild
```

**Reconcile (safe on any startup):**
```bash
python3 .claude/scripts/parse_usage.py --reconcile
```

**Audit:** JSONL transcripts are the permanent record. CSV can always be re-derived from them.

---

**Status:** Ready for worker implementation.
**Created:** 2026-06-23
