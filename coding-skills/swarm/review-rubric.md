# Swarm Review Rubric

The planner/reviewer (master agent / Opus) must inspect every worker diff before accepting. This rubric defines what to check.

**Hard rule: reviewer must not approve unless `diff.patch` and validation logs were read.**

---

## Correctness
- Does the diff solve the assigned task (as stated in `prompt.md`)?
- Does it introduce regressions? (Check `test.log`.)
- Are edge cases covered?
- Does the worker's `summary.md` match the actual diff?

## Scope
- Did the worker touch only the expected files?
- Did the worker avoid unrelated cleanup or reformatting?
- Is the diff minimal — no unnecessary churn?
- Any files modified that were listed in "Files Out of Scope"?

## Tests
- Were relevant tests run? (Check `test.log`.)
- Were test failures explained?
- Are new tests meaningful (not just passing trivially)?
- Did the test command from `prompt.md` actually run?

## Safety
- Any secrets or credentials exposed in the diff?
- Any destructive commands in the diff (rm -rf, DROP TABLE, git reset --hard)?
- Any migration or deployment risk introduced?
- Any auth, billing, or security-sensitive change touched without explicit planner approval?
- Any protected path modified (`.env`, `migrations/`, `deploy/`, `infra/`, secrets)?

## Maintainability
- Is the code readable and clear?
- Does it match existing repo style?
- Are abstractions appropriate — not over-engineered?
- Would a future maintainer understand it without context from this swarm run?

## Status Interpretation
- `done` — verify tests passed, diff is correct
- `blocked` — document blocker; do not attempt to accept diff
- `needs_review` — escalation required; run `swarm.py redispatch --run <run_id> --task <task_id>` to create a new revision
- `failed` — check stderr.log and exit_code; diagnose root cause, then run `swarm.py redispatch --run <run_id> --task <task_id>` for re-dispatch

---

## Verdict

After review, record one of:

```
APPROVED     — diff is correct, tests pass, safe to accept
NEEDS_FIXES  — specific issues found; describe exact fix needed for re-dispatch
BLOCKED      — cannot proceed without human input or missing prerequisite
```

Write verdict to `review/final-verdict.md`. Include:
- Verdict
- Evidence (which files, lines, log lines)
- For NEEDS_FIXES: exact fix description under a `## Required Fixes` heading — this heading is required so `swarm.py redispatch` can extract fix instructions programmatically
- For BLOCKED: exact blocker and required next step

**NEEDS_FIXES re-dispatch policy:**
- NEEDS_FIXES is re-dispatched to a NEW worker in a new task dir `T<N>-r<M>` via `swarm.py redispatch --run <run_id> --task <task_id>` — never the same worker/worktree.
- The revision worktree is seeded with the prior attempt's diff so the new worker only needs to address the required fixes.
- After `max_revisions` (config key `max_revisions`, default 3) revisions, redispatch escalates to human and writes `review/escalation.md` with status `BLOCKED`. No further revision is created automatically.
