# Workspace Template — Replicate the Orchestration Pattern

Minimal files to copy into a new repo and get master/worker orchestration running.
See [ORCHESTRATION_GUIDE.md](./ORCHESTRATION_GUIDE.md) for conceptual depth.

---

## Quick Copy Checklist

### Required (core orchestration)

```
CLAUDE.md                          ← routing rules; customize for your project
.claude/agents/master.md           ← master agent definition
.claude/agents/worker.md           ← worker agent definition
.claude/settings.json              ← hook registration (required if using hooks)
```

### Optional (token tracking)

```
.claude/hooks/session_start.sh     ← runs parse_usage.py --reconcile on session open
.claude/hooks/session_end.sh       ← runs parse_usage.py --transcript on session close
.claude/scripts/parse_usage.py     ← JSONL → usage.csv parser
.claude/TOKEN_TRACKING_PLAN.md     ← design doc; informational only
```

### Skip (local session data / compiled artifacts)

```
.claude/usage.csv                  ← generated; do not copy
.claude/.parsed_sessions.json      ← generated sidecar; do not copy
.claude/scripts/__pycache__/       ← compiled Python; do not copy
.claude/settings.local.json        ← machine-local overrides; do not copy
```

---

## File-by-File Reference

### `CLAUDE.md` — KEEP, MODIFY

The routing brain. The main Claude Code thread reads this on every message and
routes automatically. Contains:

- Which tasks go to `master` vs `worker`.
- The plan → implement → review → fix loop rules.
- The "always" rules (full context, absolute paths, no human routing decisions).

**Modify:** Keep the Agent Delegation section structure intact. Add or reword
routing rules for your domain (e.g. "database migration tasks → master"). Remove
examples irrelevant to your project.

---

### `.claude/agents/master.md` — KEEP, MODIFY LIGHTLY

Defines the `master` subagent (opus, high effort, no Edit/Write tools).

Key frontmatter:

```yaml
---
name: master
model: claude-opus-4-8
effort: high
tools: Read, Glob, Grep, Bash     # no Edit/Write — enforces "master never codes"
skills:
  - caveman:full
  - diffwarden
---
```

**Modify:** Adjust the system prompt body if your master role differs. Do not
add `Edit` or `Write` to tools — that guardrail is intentional.

---

### `.claude/agents/worker.md` — KEEP, MODIFY LIGHTLY

Defines the `worker` subagent (sonnet, medium effort, full edit tools).

Key frontmatter:

```yaml
---
name: worker
model: claude-sonnet-4-6
effort: medium
tools: Read, Glob, Grep, Edit, MultiEdit, Write, Bash
skills:
  - caveman:full
  - diffwarden
---
```

**Modify:** Add project-specific constraints (e.g. "never edit migrations
without approval"). Keep the `## Output Format` block — master's review loop
depends on reading `DONE | NEEDS CLARIFICATION | BLOCKED` from worker output.

---

### `.claude/settings.json` — KEEP, UPDATE PATHS

Registers hooks with Claude Code. Template:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/session_start.sh"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/session_end.sh"
          }
        ]
      }
    ]
  }
}
```

`${CLAUDE_PROJECT_DIR}` expands to the project root at runtime. No path edits
needed if you copy the file verbatim and keep the hooks in `.claude/hooks/`.

**If skipping token tracking:** remove the `SessionStart`/`SessionEnd` blocks.
The `SubagentStart` debug block (present in this workspace) is also optional —
safe to remove.

---

### `.claude/hooks/session_start.sh` — OPTIONAL, NO EDITS NEEDED

Runs `parse_usage.py --reconcile` on session open. Catches transcripts that
were missed if a previous session's `SessionEnd` hook failed.

Non-fatal by design — errors are logged to stderr, hook exits 0 so Claude Code
session continues.

---

### `.claude/hooks/session_end.sh` — OPTIONAL, NO EDITS NEEDED

Receives transcript path from Claude Code via stdin JSON, calls
`parse_usage.py --transcript <path>`. Requires `jq` on PATH.

⚠️ Note: Unlike session_start, session_end.sh fails non-zero if jq/parser
missing or parse fails. Claude Code logs the error but does not block the
session.

---

### `.claude/scripts/parse_usage.py` — OPTIONAL, UPDATE TRANSCRIPTS_GLOB

Parses JSONL transcripts → `.claude/usage.csv`. Requires Python 3.8+.

Update the `TRANSCRIPTS_GLOB` variable value near the top of the file — change
the `~/.claude/projects/<slug>/*.jsonl` path to match your new project's
transcript dir:

```python
TRANSCRIPTS_GLOB = os.path.expanduser(
    "~/.claude/projects/<your-project-slug>/*.jsonl"
)
```

The project slug is the filesystem-escaped path to your project root. Claude
Code derives it from the absolute path of your workspace. Find it by running:

```bash
ls ~/.claude/projects/
```

After your first session in the new workspace, a directory with the slug will
appear there.

Modes:
- `--transcript <path>` — parse single file (called by session_end.sh)
- `--reconcile` — parse transcripts not yet recorded in the sidecar ledger (.parsed_sessions.json), independent of CSV mtime (called by session_start.sh)
- `--rebuild` — wipe CSV and reparse everything from scratch

---

### `.claude/TOKEN_TRACKING_PLAN.md` — SKIP or KEEP as reference

Design notes for the token parser. No runtime effect. Informational only.

---

## How to Customize

### Swap models

Edit frontmatter in the agent `.md` files:

```yaml
model: claude-sonnet-4-6   # or claude-haiku-4-5, claude-opus-4-8, etc.
effort: low | medium | high
```

### Add a third agent (e.g. a security reviewer)

Create `.claude/agents/security.md` with frontmatter. Add a routing rule to
`CLAUDE.md`:

```
### Route to `security` for:
- Auth/authz changes
- Dependency updates with CVEs
```

### Tighten the review gate

In worker's system prompt, change the pre-DONE step:

```
Before DONE: run `/dw loop --max 5 --security` instead of `/dw loop`
```

For PRs: master runs `/dw review #<num>` instead of `/dw review workspace`.

### Hook into CI instead of Claude Code hooks

If you run in headless/CI environments where `SessionEnd` doesn't fire, call
the parser directly from your CI script:

```bash
python3 .claude/scripts/parse_usage.py --reconcile
```

Or rebuild from scratch:

```bash
python3 .claude/scripts/parse_usage.py --rebuild
```

---

## Gotchas

**session_end.sh must be executable.**
`session_end.sh` is invoked directly in `settings.json` (no `bash` prefix). It
must be executable: `chmod +x .claude/hooks/session_end.sh`. If you copy/unzip
the template, the exec bit may be lost.

**Relative paths in settings.json won't work.**
Use `${CLAUDE_PROJECT_DIR}` (Claude Code env var) or absolute paths in hook
commands. Relative paths resolve against the shell's cwd at hook time, which
varies.

**TRANSCRIPTS_GLOB must match your actual project slug.**
Claude Code names the transcript directory after the escaped absolute path of
your workspace. If you move or rename the workspace, update this glob or run
`--rebuild` to re-scan.

**Python version for parse_usage.py.**
Tested on Python 3.8+; may work on 3.6+ (f-strings, `os.replace` required) but
not guaranteed. Check with `python3 --version`.

**`__pycache__` from parse_usage.py is local.**
Do not commit it. Add `.claude/scripts/__pycache__/` to `.gitignore`.

**usage.csv and .parsed_sessions.json are derived, not source.**
Commit them if you want to persist history across machines. Otherwise add to
`.gitignore` and treat them as ephemeral — `--rebuild` regenerates from
transcripts.

**settings.local.json is machine-local.**
Contains per-machine overrides. Do not commit. Add to `.gitignore`.

**The `caveman` and `diffwarden` skills must be installed separately.**
Agent `.md` files declare them in frontmatter (`skills: [caveman:full,
diffwarden]`) but Claude Code only loads installed skills. Install both before
testing the orchestration:

- `diffwarden`: follow install instructions at https://github.com/jperocho/diffwarden
- `caveman`: install per your team's skill distribution

If you don't have the caveman skill/plugin installed, you can remove
`caveman:full` from agent frontmatter in `master.md` and `worker.md` — agents
work without it, output just won't be compressed.

**Tool list in agent frontmatter is a hard guardrail.**
Master lacks `Edit`/`Write` by design. Do not add them "just in case" — that
removes the structural enforcement of "master never writes code."

---

## Verify: Test Orchestration Works

After copying files, send one small multi-step request and confirm this sequence
fires automatically (no `@master` or `@worker` typed):

1. Main thread routes to **master** for a plan.
2. Master outputs `## Plan` + `## Risks` + `## Decision Points` in caveman mode.
3. Main thread hands plan to **worker** for implementation.
4. Worker outputs `## Task` / `## Changes` / `## Validation` / `## Next Step DONE`.
5. Main thread sends result back to **master** for review.
6. Master outputs `## Findings` + `## Verdict APPROVED`.

Minimal test prompt:

```
Add a hello() function to a new file hello.py that prints "hello world". Include a test.
```

Expected flow: master plans small task with no blocking decision points → worker
writes files + runs test + `/dw loop workspace` → master reviews + APPROVED.

If routing doesn't fire (main thread answers directly instead of delegating),
check that `CLAUDE.md` is in the project root and the Agent Delegation section
is syntactically intact.
