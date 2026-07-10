---
name: swarm
description: Multi-agent orchestration workflow. Activate with `/swarm <task>` to plan, dispatch, and review work across codex, opencode, and sonnet executors. Planner/reviewer role = master agent. Implementation = worker agent or claude -p invocation. tmux NOT used; subprocess only.
version: 0.1.0
author: lars@offshorly.com
---

# /swarm — Multi-Agent Orchestration Skill

Activate with `/swarm <task description>`.

## Overview

`/swarm` routes tasks across specialized executors, isolates work in git worktrees, collects diffs/logs, and requires planner review before any change is accepted.

**Planner/Reviewer** = the existing `master` agent (see `/home/lars-lenon/Desktop/offshorly-dev/My-AI-Boilerplate/configurations/ai-open-orchestrator-lab/claude-orchestration/`). Never duplicated here; referenced as source of truth.

**Sonnet executor** = the existing `worker` agent or a `claude -p <prompt>` non-interactive invocation.

**tmux is NOT available** in this environment. All subprocess execution uses `subprocess.Popen`/`subprocess.run` only.

---

## 12-Step Workflow

1. **Receive goal.** Treat the user's `/swarm <goal>` text as the main objective.
2. **Inspect repo.** Run `git rev-parse --show-toplevel`, detect repo name, test commands, and protected paths.
3. **Load config.** Read `.claude/swarm.config.json` if present; merge with `~/.claude/swarm/config.json` defaults.
4. **Create run directory.** Under `.swarm/runs/<timestamp>-<slug>/` (per-repo) or `~/.claude/swarm/runs/<repo>-<timestamp>-<slug>/` (global fallback).
5. **Plan work.** Planner (master agent / Opus) inspects repo, creates task graph, chooses executors per routing table. No workers launched until plan exists.
6. **Split into tasks.** Each task gets its own `tasks/T<N>/` directory with `prompt.md` rendered from the handoff template.
7. **Route tasks.** Assign each task to cheapest capable executor per routing table and escalation rules.
8. **Create worktrees.** Each write-capable worker gets `git worktree add .swarm/worktrees/<run_id>/<task_id> -b swarm/<run_id>/<task_id>`. Read-only scouts use the main repo.
9. **Launch executors.** Run adapters via subprocess. Cap at 3 parallel workers by default (override via config `default_parallelism`).
10. **Collect diffs and logs.** After each worker: `git diff` → `diff.patch`, capture stdout/stderr, write `status.json`.
11. **Review with planner.** Master agent reviews every diff and log before accepting. Worker output is never self-approved. When the reviewer returns NEEDS_FIXES: run `swarm.py redispatch --run <run_id> --task <task_id>` — this creates a fresh task dir `T<N>-r<M>` with a new subprocess worker, seeds the new worktree with the prior attempt's diff, and carries fix instructions forward from `review/final-verdict.md`'s `## Required Fixes` section. Each redispatch increments the revision counter. After `max_revisions` (config, default 3) the redispatch command escalates to human by writing `review/escalation.md` and setting status `blocked` — no further revision is created automatically.
11b. **Accept & merge back.** After the reviewer returns APPROVED, run `swarm.py accept --run <run_id>` to apply the diff to the current branch (uncommitted by default), enforce protected-path checks, and remove the worktree and temp branch. This happens automatically once review passes; no additional human confirmation is required at this step. Use `--commit` to opt into an auto-commit. If a patch touches a protected path, accept refuses that task and preserves the worktree for manual handling. If a patch does not apply cleanly (context drift), accept prints the error, keeps the worktree, and moves to the next task.
12. **Produce final summary.** Write `review/final-verdict.md`, collect `applied/accepted.patch`, list unresolved risks and next actions.

---

## Executor Routing Table

| Executor | Real model/CLI | Use for |
|---|---|---|
| `codex-gpt5.5` | `codex exec -m gpt-5.5` | normal implementation, multi-file changes, bug fixes, refactors requiring stronger reasoning, backend/API changes, test repair |
| `deepseek-v4-flash` | `opencode run -m opencode/deepseek-v4-flash-free` | read-only scouting, grep-heavy exploration, second opinions, alternative plans, performance ideas |
| `sonnet` | `claude -p` (non-interactive print mode) | Fallback executor — used when codex and deepseek are both unavailable, when a task genuinely requires Claude Code native tool use, or by explicit override for docs/UI-polish tasks where quality is prioritized over cost. |
| `opus/master` | master agent (planner/reviewer only) | architecture, task decomposition, routing, root-cause diagnosis, final review, merge decision |

**Disabled/unavailable aliases (do not use):**
- `codex-5.4-mini` — label from PLAN.md, NOT a real model in this environment. Alias of gpt-5.5, disabled.
- `codex-5.4` — label from PLAN.md, NOT a real model in this environment. Alias of gpt-5.5, disabled.

---

## Hard Rules

```
Never let workers approve their own work.
Never run destructive commands without human confirmation.
Never commit, push, deploy, run migrations, delete files broadly, or modify secrets without explicit approval.
Prefer worktrees for parallel write tasks.
Use read-only mode for scouting workers (opencode default).
Cap parallel workers at 3 by default. Override only through config.
tmux is NOT used. Use subprocess.Popen/subprocess.run only.
Planner decides. Workers execute. Reviewer verifies. Human approves destructive actions.
codex runs with sandbox_mode: danger-full-access in this container because bwrap cannot create user namespaces at the OS level (unfixable by swarm). Isolation is provided by worktree isolation, mandatory review gate, and protected-path enforcement at accept-time — not codex's own sandbox.
```

---

## Usage Patterns

```
/swarm fix the failing tests
/swarm implement the auth middleware from issue #123
/swarm scout why the parser fails
/swarm plan only: refactor the importer pipeline
/swarm status
/swarm doctor
/swarm install repo
```

## CLI Entry Point

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py doctor
python3 ~/.claude/skills/swarm/scripts/swarm.py install-repo <path>
python3 ~/.claude/skills/swarm/scripts/swarm.py status --run <run_id>
python3 ~/.claude/skills/swarm/scripts/swarm.py run-one --goal "<goal>" --executor codex
python3 ~/.claude/skills/swarm/scripts/swarm.py redispatch --run <run_id> --task T001 [--executor sonnet] [--verdict-file review/final-verdict.md]
```
