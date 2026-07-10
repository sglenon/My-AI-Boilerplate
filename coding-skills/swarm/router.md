# Swarm Router — Routing and Escalation Logic

## Model Name Reality Check

PLAN.md references `codex-5.4-mini` and `codex-5.4`. These are **not real model names** in this environment. The real default codex model is `gpt-5.5`. Config entries for `codex-5.4-mini`/`codex-5.4` exist but are `"enabled": false`. All active codex routing uses `gpt-5.5`.

DeepSeek routes to `opencode/deepseek-v4-flash-free` via opencode CLI.

---

## Routing Rules

### Use Opus/Master (Planner — never writes code) for:
- Ambiguous tasks where requirements are unclear
- Architecture and design decisions
- Task decomposition and plan creation
- Final review of every worker diff
- Dangerous operations (auth, billing, migrations, deployment, infrastructure, secrets)
- Root-cause diagnosis spanning multiple files
- Resolving worker disagreements

### Use Codex (gpt-5.5) for:
- Normal implementation requiring code reasoning
- Multi-file bug fixes
- Test suite repair when failure cause is non-obvious
- API/backend changes
- Medium-to-large refactors
- Contained edits with predictable scope
- Repetitive mechanical changes
- Docs, prose, consistency, and UI-copy tasks (default; sonnet by explicit override for quality, or if codex unavailable)

### Use DeepSeek v4 Flash via opencode for:
- Read-only scouting (default, write NOT allowed)
- Cheap parallel repo exploration
- Finding relevant files and symbols
- Proposing hypotheses and alternative approaches
- Generating candidate plans
- Second opinions on implementation strategies
- Performance investigation ideas

### Use Sonnet (claude -p) for:
- **Last-resort fallback:** when codex (gpt-5.5) AND opencode/deepseek are both unavailable
- **Claude Code native tool use:** when a task genuinely requires Claude Code's native file/tool access
- **Explicit override:** docs/UI-polish tasks where quality is prioritized over cost (human or planner must explicitly override to sonnet; codex is the default for docs)

---

## Escalation Rules

Escalate back to planner (master agent) when any of these hold:

- Worker reports uncertainty or blocked status
- Tests fail for unclear reason
- Diff touches more files than the task specified
- Task scope expands beyond original assignment
- Worker modifies a protected file (`.env`, secrets, migrations, deploy scripts)
- Task requires product or domain judgment
- Two workers produce materially different implementations
- Exit code non-zero with ambiguous cause
- Worker output contains auth failure markers

---

## Revision Routing

When a reviewer returns NEEDS_FIXES:

- The original task (e.g. `T001`) keeps its task dir; no changes are made to it.
- A new task dir is created with a revision suffix: `T001-r2`, `T001-r3`, etc.
- The new revision's worktree is seeded with the prior attempt's `diff.patch` so the new worker starts from a patched state and only needs to address the required fixes.
- Trigger with: `swarm.py redispatch --run <run_id> --task T001`
- The revision MAY route to a different or stronger executor than the original via `--executor` override (e.g. codex→sonnet after repeated failure).
- Revisions are bounded by `max_revisions` (config key, default 3). After `max_revisions` attempts, redispatch writes `review/escalation.md`, sets the task status to `blocked`, and returns exit code 1 — escalating to master/human for manual intervention. No further task dir is created.

---

## Task Size Heuristics

| Task scope | Recommended executor |
|---|---|
| Single-file, obvious fix | codex (gpt-5.5) |
| Multi-file, scoped | codex (gpt-5.5) |
| Read-only investigation | deepseek via opencode |
| Docs / prose / consistency | codex (gpt-5.5) — sonnet by explicit override for quality, or if codex unavailable |
| Architecture / review / diagnosis | master (opus) |

---

## Parallelism Rules

- Max 3 parallel workers by default (config: `default_parallelism`).
- Read-only scouts may run in parallel freely.
- Write workers each need their own worktree.
- Never two write workers in the same worktree.
- If a third parallel write task is needed, queue it until a slot frees.
