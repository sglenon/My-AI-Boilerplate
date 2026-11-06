# Core Concepts

This guide explains the building blocks of Claude Code so you understand what each folder in this repo does and why.

---

## CLAUDE.md

A `CLAUDE.md` file is a plain text file that Claude Code reads automatically at the start of every session in that directory. It loads rules, context, and routing instructions into the conversation before you type anything — think of it as a standing brief that Claude always has open. Without it, Claude has no project context; with it, Claude follows your team's conventions and delegates work to the right agents automatically.

**Look at:** `CLAUDE.md` in the repo root, and `configurations/global-coding-rules/CLAUDE.md` for a reusable template you can copy into your own project.

---

## Skills

A skill is a folder that contains a `SKILL.md` file. The SKILL.md describes a specific, repeatable task — reviewing security, generating a spec, explaining code — and tells Claude exactly how to perform it. Skills make knowledge reusable: write the workflow once, install the folder, and any project can call it. You invoke a skill by typing `/<skill-name>` or just asking Claude in plain language.

Install to all projects: copy the folder to `~/.claude/skills/<name>/`.
Install to one project: copy the folder to `<project>/.claude/skills/<name>/`.

**Look at:** `coding-skills/explain-code/` for a simple single-purpose skill, and `.claude/skills/speckit/SKILL.md` for the overview of the full speckit spec-driven workflow.

---

## Subagents (master / worker)

A subagent is a named AI role defined in a Markdown file inside `.claude/agents/`. Each file sets a model, a reasoning level, and a specific mandate — for example, `master.md` plans and reviews while `worker.md` implements and writes code. Claude reads the `CLAUDE.md` routing rules to decide which subagent to delegate each task to, then hands off context automatically. Separating roles keeps AI work safer and more predictable: a planning agent never writes code, and an implementation agent never approves its own output.

**Look at:** `orchestration/core/.claude/agents/` — it contains `master.md`, `worker.md`, `commit.md`, and `sonar.md` as a complete working example.

---

## Hooks

Hooks are shell scripts that Claude Code runs automatically at defined points in a session: when a session starts, when it ends, or before and after specific tool calls. They let you automate setup (activating a virtual environment, loading secrets from a safe store), teardown (writing session summaries), or quality gates (running a linter before Claude edits a file). Hooks are configured in `.claude/settings.json` under `hooks`.

**Look at:** `orchestration/core/.claude/hooks/` — it contains `bootstrap.sh`, `session_start.sh`, and `session_end.sh`; and `orchestration/core/.claude/settings.json` where those hooks are wired up.

---

## Orchestration / Swarm

Orchestration means using multiple AI agents in a structured pipeline. In this repo there are two patterns. The first is the `orchestration/core/` package: a master agent plans and reviews, a worker agent implements, a sonar agent runs static analysis, and a commit agent handles git. The second is the `swarm` skill: a lightweight multi-agent workflow where Claude dispatches parallel tasks to separate executor processes (codex, opencode, sonnet) and then reviews and merges their output. Both patterns improve quality by forcing separation of planning, implementation, and review into distinct roles that check each other.

**Look at:** `orchestration/README.md` and `orchestration/core/` for the installable pipeline; `coding-skills/swarm/` for the swarm skill; `.swarm/README.md` for how swarm runs are stored locally.
