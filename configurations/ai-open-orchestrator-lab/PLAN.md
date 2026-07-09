# Build and Install `/swarm`: Multi-Agent Claude Code Orchestration Across All Repos

You are my Claude Code setup agent.

Your job is to CREATE, IMPLEMENT, VALIDATE, and SET UP a reusable `/swarm` workflow for all of my coding repos.

I want a Claude Code-native workflow where:

* Claude Opus/Fable acts as the planner, architect, router, and final reviewer.
* Implementation is delegated to cheaper/faster executors depending on task type:

  * Codex 5.4-mini
  * Codex 5.4
  * DeepSeek v4 Flash via opencode
  * Claude Sonnet
* The workflow activates when I type `/swarm <task>`.
* It should work across all my repos with minimal per-repo setup.
* It should use safe worktree/task isolation so multiple workers do not destroy the same working tree.
* It should preserve logs, diffs, task prompts, test outputs, and final review notes.
* It should not blindly trust worker output.
* It should never let an implementation worker approve its own work.

Treat this as infrastructure. Build it carefully.

---

## 0. Working Principles

Use this architecture:

```text
Claude Code
└── /swarm <goal>
    ├── Planner/Reviewer: Opus/Fable
    │   ├── inspect repo
    │   ├── create task graph
    │   ├── choose executors
    │   ├── review outputs
    │   └── approve or re-dispatch fixes
    ├── Dispatcher
    │   ├── creates run folder
    │   ├── creates task files
    │   ├── launches workers
    │   ├── monitors status
    │   └── collects reports
    ├── Workers
    │   ├── codex-5.4-mini
    │   ├── codex-5.4
    │   ├── deepseek-v4-flash via opencode
    │   └── sonnet
    └── Final output
        ├── approved diff
        ├── validation logs
        ├── unresolved risks
        └── next actions
```

Core invariant:

```text
Planner decides.
Workers execute.
Reviewer verifies.
Human approves destructive actions.
```

Do not implement a chaotic “many agents edit same repo” setup. Use git worktrees or isolated task folders for implementation workers. If worktree isolation is not possible for a repo, degrade to sequential execution and explain why.

---

## 1. Inspect My Environment First

Before writing files, inspect the machine and repo environment.

Run or equivalent:

```bash
pwd
uname -a || ver
git --version
python3 --version || python --version
node --version
npm --version
tmux -V
claude --version || true
codex --version || true
opencode --version || true
```

Also inspect available Claude Code directories:

```bash
ls -la ~/.claude || true
find ~/.claude -maxdepth 3 -type d | sort || true
```

Then inspect the current repo:

```bash
git rev-parse --show-toplevel
git status --short
find . -maxdepth 3 -type f \( -name "package.json" -o -name "pyproject.toml" -o -name "requirements.txt" -o -name "Cargo.toml" -o -name "go.mod" -o -name "CLAUDE.md" \) | sort
```

Do not assume exact CLI flags for `codex`, `opencode`, or `claude`. Read their help first:

```bash
codex --help || true
opencode --help || true
claude --help || true
```

If a tool is missing, do not fake success. Install only safe prerequisites when reasonable. If authentication is required, stop and ask me to authenticate.

---

## 2. Codex Plugin Setup

I want Codex usable from inside Claude Code where possible.

Check whether Claude Code plugin commands are available. If they are available, run or guide me through:

```text
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```

If these slash commands cannot be executed from your current context, create a clear setup note at:

```text
~/.claude/swarm/CODEX_PLUGIN_SETUP.md
```

Include:

```text
1. Open Claude Code.
2. Run:
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup

3. Authenticate with my ChatGPT/Codex account when prompted.
4. Verify Codex works inside Claude Code.
```

Also verify whether a Codex subagent or command like `codex:codex-rescue` exists. If it exists, register it as an available executor. If it does not exist, continue using the local Codex CLI adapter.

Do not change project code during authentication/setup.

---

## 3. Target File Layout

Create a global reusable skill and shared runner scripts here:

```text
~/.claude/
  skills/
    swarm/
      SKILL.md
      router.md
      handoff-template.md
      review-rubric.md
      troubleshooting.md
      scripts/
        swarm.py
        adapters/
          base.py
          codex.py
          opencode.py
          sonnet.py
        lib/
          repo.py
          tasks.py
          worktrees.py
          logging.py
          shell.py
          config.py
  swarm/
    config.json
    repos.json
    logs/
    runs/
```

Then create lightweight per-repo config files in each repo:

```text
<repo>/
  .claude/
    swarm.config.json
  .swarm/
    README.md
```

If `.claude/skills/swarm/SKILL.md` is required project-locally for `/swarm` to appear, create a project-level shim that points to the global skill. Prefer the global skill as source of truth so updates apply across all repos.

---

## 4. Create the `/swarm` Skill

Create:

```text
~/.claude/skills/swarm/SKILL.md
```

It should define `/swarm` as a workflow skill.

The skill must instruct Claude Code to:

1. Treat the user’s `/swarm <goal>` text as the main goal.
2. Inspect the current repo.
3. Load `.claude/swarm.config.json` if present.
4. Create a run directory under `.swarm/runs/<timestamp>-<slug>/` or `~/.claude/swarm/runs/<repo>-<timestamp>-<slug>/`.
5. Plan the work before spawning workers.
6. Split work into task files.
7. Route each task to the cheapest capable executor.
8. Use worktrees for implementation workers.
9. Collect diffs and logs.
10. Review everything with Opus/Fable before applying or accepting.
11. Re-dispatch fixes when needed.
12. Produce a final summary.

The skill should include this routing table:

```text
Executor routing:

codex-5.4-mini:
- small scoped bugs
- test fixes
- mechanical refactors
- simple single-file or narrow multi-file edits
- cheap first-pass implementation

codex-5.4:
- normal implementation
- multi-file changes
- debugging with code edits
- refactors requiring stronger reasoning
- backend/API changes
- test repair when failure cause is non-obvious

deepseek-v4-flash via opencode:
- cheap repo exploration
- grep-heavy scouting
- second opinions
- alternative implementation plans
- performance ideas
- read-only investigation by default

sonnet:
- Claude-native implementation
- repo edits that benefit from Claude Code’s native tools
- frontend polish
- documentation/codebase consistency tasks
- fallback when Codex/opencode are unavailable

opus/fable planner:
- architecture
- task decomposition
- routing
- root-cause diagnosis
- final review
- merge decision
- human-facing explanation
```

The skill must enforce:

```text
Never let workers approve their own work.
Never run destructive commands without human confirmation.
Never commit, push, deploy, run migrations, delete files broadly, or modify secrets without approval.
Prefer worktrees for parallel implementation.
Use read-only mode for scouting workers.
Cap parallel workers at 3 by default.
Allow parallelism override only through config.
```

---

## 5. Create Router Documentation

Create:

```text
~/.claude/skills/swarm/router.md
```

Content should define detailed routing logic.

Include:

```text
Use Opus/Fable directly for:
- ambiguous tasks
- architecture
- decomposition
- final review
- dangerous operations
- tasks touching auth, billing, database migrations, deployment, infrastructure, secrets

Use Codex 5.4-mini for:
- contained edits
- predictable tests
- obvious failures
- narrow refactors
- repetitive changes

Use Codex 5.4 for:
- implementation requiring stronger code reasoning
- multi-file bug fixes
- test suite repair
- API/backend changes
- medium-sized refactors

Use DeepSeek v4 Flash via opencode for:
- read-only scouting
- cheap parallel exploration
- finding files
- proposing hypotheses
- comparing approaches
- generating candidate plans

Use Sonnet for:
- Claude-native file edits
- docs and repo-specific consistency
- UI polish
- fallback executor
```

Add escalation rules:

```text
Escalate back to planner when:
- worker reports uncertainty
- tests fail for unclear reason
- diff touches more files than expected
- task scope expands
- worker modifies protected files
- task requires product/domain judgment
- two workers disagree materially
```

---

## 6. Create Handoff Template

Create:

```text
~/.claude/skills/swarm/handoff-template.md
```

Every worker task must be written like this:

```md
# Swarm Worker Task

## Run
- run_id:
- task_id:
- repo:
- base_branch:
- worktree:
- executor:

## Goal
<one narrow goal>

## Context
<relevant repo context, files, commands, errors, constraints>

## Files In Scope
- <path>
- <path>

## Files Out of Scope
- <path>
- <path>

## Constraints
- Do not commit.
- Do not push.
- Do not deploy.
- Do not modify secrets.
- Do not edit files outside scope unless necessary; if necessary, explain why.
- Keep changes minimal.
- Prefer tests.

## Required Output
Write these files:
- status.json
- summary.md
- diff.patch
- test.log
- notes.md

## Validation Command
<repo-specific test command>

## Stop Conditions
Stop when:
- task is complete and tests pass
- blocked by missing dependency/auth
- scope becomes larger than assigned
- destructive action is required
```

---

## 7. Create Review Rubric

Create:

```text
~/.claude/skills/swarm/review-rubric.md
```

Reviewer must check:

```text
Correctness:
- Does the diff solve the assigned task?
- Does it introduce regressions?
- Are edge cases covered?

Scope:
- Did worker touch only expected files?
- Did worker avoid unrelated cleanup?
- Is the diff minimal?

Tests:
- Were relevant tests run?
- Were failures explained?
- Are new tests meaningful?

Safety:
- Any secrets exposed?
- Any destructive commands?
- Any migration/deployment risk?
- Any auth/billing/security-sensitive change?

Maintainability:
- Is code readable?
- Does it match repo style?
- Are abstractions appropriate?
- Is there overengineering?

Verdict:
- APPROVED
- NEEDS_FIXES
- BLOCKED
```

Reviewer must not approve unless the diff and validation logs were inspected.

---

## 8. Implement the Swarm Runner

Create:

```text
~/.claude/skills/swarm/scripts/swarm.py
```

This should be the main dispatcher.

It must support:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py init
python3 ~/.claude/skills/swarm/scripts/swarm.py doctor
python3 ~/.claude/skills/swarm/scripts/swarm.py plan "<goal>"
python3 ~/.claude/skills/swarm/scripts/swarm.py dispatch --plan <plan.json>
python3 ~/.claude/skills/swarm/scripts/swarm.py status --run <run_id>
python3 ~/.claude/skills/swarm/scripts/swarm.py collect --run <run_id>
python3 ~/.claude/skills/swarm/scripts/swarm.py install-repo <path>
python3 ~/.claude/skills/swarm/scripts/swarm.py install-all --roots "<root1>:<root2>"
```

If full implementation is too large, build MVP first:

```text
MVP commands:
- init
- doctor
- install-repo
- status
- run-one
```

But still create the full architecture skeleton.

Runner responsibilities:

```text
- detect repo root
- load global config
- load repo config
- create run directory
- create task directory
- create worktree when needed
- write worker prompt
- launch executor adapter
- capture stdout/stderr
- write status files
- collect git diff
- clean up safely
```

Use Python standard library where possible.

Do not require heavy dependencies unless necessary.

---

## 9. Implement Config Files

Create global config:

```text
~/.claude/swarm/config.json
```

Suggested content:

```json
{
  "version": 1,
  "default_parallelism": 3,
  "max_parallelism": 5,
  "require_worktrees_for_writes": true,
  "default_timeout_minutes": 45,
  "protected_globs": [
    ".env",
    ".env.*",
    "**/*secret*",
    "**/*credential*",
    "**/id_rsa",
    "**/id_ed25519",
    "**/node_modules/**",
    "**/.git/**"
  ],
  "executors": {
    "codex-5.4-mini": {
      "enabled": true,
      "adapter": "codex",
      "model": "codex-5.4-mini",
      "effort": "medium",
      "write_allowed": true,
      "max_parallel": 3
    },
    "codex-5.4": {
      "enabled": true,
      "adapter": "codex",
      "model": "codex-5.4",
      "effort": "high",
      "write_allowed": true,
      "max_parallel": 2
    },
    "deepseek-v4-flash": {
      "enabled": true,
      "adapter": "opencode",
      "model": "deepseek-v4-flash",
      "effort": "medium",
      "write_allowed": false,
      "max_parallel": 3
    },
    "sonnet": {
      "enabled": true,
      "adapter": "sonnet",
      "model": "sonnet",
      "effort": "medium",
      "write_allowed": true,
      "max_parallel": 2
    }
  }
}
```

Important: verify actual model names and CLI model flags. If these names are not valid in the installed tools, keep them configurable and update config with the valid names.

Create per-repo config template:

```json
{
  "version": 1,
  "repo_name": "<auto-detect>",
  "test_commands": {
    "default": "<auto-detect>",
    "unit": "<auto-detect>",
    "lint": "<auto-detect>"
  },
  "protected_paths": [
    ".env",
    ".env.*",
    "migrations/",
    "deploy/",
    "infra/"
  ],
  "preferred_executors": {
    "small_fix": "codex-5.4-mini",
    "implementation": "codex-5.4",
    "scouting": "deepseek-v4-flash",
    "docs": "sonnet",
    "fallback": "sonnet"
  },
  "parallelism": 3
}
```

Auto-detect common test commands:

```text
package.json + npm test     → npm test
package.json + pnpm         → pnpm test
pyproject.toml              → pytest
requirements.txt            → pytest
Cargo.toml                  → cargo test
go.mod                      → go test ./...
```

If uncertain, set test command to empty and mark validation as manual.

---

## 10. Implement Adapters

Create adapter files:

```text
~/.claude/skills/swarm/scripts/adapters/base.py
~/.claude/skills/swarm/scripts/adapters/codex.py
~/.claude/skills/swarm/scripts/adapters/opencode.py
~/.claude/skills/swarm/scripts/adapters/sonnet.py
```

Each adapter must expose a common interface:

```python
class ExecutorAdapter:
    name: str

    def available(self) -> bool:
        ...

    def version(self) -> str:
        ...

    def run_task(self, task_dir: Path, worktree_dir: Path, config: dict) -> int:
        ...
```

Adapter behavior:

```text
codex.py:
- Verify codex CLI exists.
- Read `codex --help` before choosing flags.
- Use configured model if supported.
- Feed worker prompt from task prompt file.
- Capture stdout/stderr.
- Do not assume auth; detect auth failure and report.

opencode.py:
- Verify opencode exists.
- Read `opencode --help`.
- Use configured DeepSeek model if supported.
- Default to read-only scouting unless task explicitly allows write.
- Capture output.

sonnet.py:
- Verify claude CLI exists.
- Read `claude --help`.
- Run as a focused Claude worker where possible.
- If CLI cannot run non-interactively, write instructions explaining manual fallback.
```

Do not hardcode brittle CLI syntax. Discover available flags and use conservative defaults.

---

## 11. Use Git Worktrees for Write Tasks

For each write-capable worker task:

```bash
git worktree add .swarm/worktrees/<run_id>/<task_id> -b swarm/<run_id>/<task_id>
```

Rules:

```text
- Each implementation worker gets its own worktree.
- Read-only scout workers may use the main repo or a read-only copy.
- Workers do not commit.
- Dispatcher collects diff using `git diff`.
- Reviewer decides whether to apply patch to main working tree.
- If two patches conflict, planner resolves merge order.
```

Implement safe cleanup:

```bash
git worktree list
git worktree remove <path>
git branch -D swarm/<run_id>/<task_id>
```

Never delete worktrees automatically unless:

* task is approved and patch is collected, or
* user explicitly requests cleanup, or
* cleanup is for an empty failed setup worktree.

---

## 12. Logging and Run Artifacts

Every `/swarm` run should create:

```text
.swarm/runs/<run_id>/
  goal.md
  plan.md
  plan.json
  router-decisions.md
  tasks/
    T001/
      prompt.md
      status.json
      stdout.log
      stderr.log
      summary.md
      diff.patch
      test.log
      notes.md
    T002/
      ...
  review/
    review.md
    findings.json
    final-verdict.md
  applied/
    accepted.patch
  swarm.log
```

`status.json` schema:

```json
{
  "run_id": "",
  "task_id": "",
  "executor": "",
  "status": "pending|running|done|failed|blocked|needs_review",
  "started_at": "",
  "finished_at": "",
  "worktree": "",
  "exit_code": null,
  "tests_passed": null,
  "summary": ""
}
```

---

## 13. Add Hooks Carefully

Use hooks only for deterministic safety and convenience, not for fuzzy orchestration.

Create or update:

```text
~/.claude/settings.json
```

or project-level:

```text
.claude/settings.json
```

Potential hooks:

```text
SessionStart:
- Run swarm doctor lightly.
- Warn if codex/opencode/tmux missing.
- Do not block session unless critical.

PreToolUse:
- Block dangerous commands unless explicitly approved:
  - rm -rf
  - git reset --hard
  - git clean -fd
  - force push
  - direct edits to .env/secrets
  - production deploy commands
  - database migration commands

PostToolUse:
- Optionally format changed files, only if repo already has formatter config.

SessionEnd:
- Summarize unfinished swarm runs.
```

Do not overdo hooks. Hooks are guardrails, not the orchestrator.

---

## 14. Build the Installers

Implement:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py install-repo <repo_path>
```

This should:

1. Verify `<repo_path>` is a git repo.
2. Create `.claude/` if missing.
3. Create `.claude/swarm.config.json` if missing.
4. Create `.swarm/README.md`.
5. Detect test commands.
6. Add `.swarm/runs/` and `.swarm/worktrees/` to `.gitignore` unless already ignored.
7. Avoid overwriting existing files without backup.
8. Print what changed.

Implement:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py install-all --roots "<paths>"
```

This should:

1. Discover git repos under the given roots.
2. Skip `node_modules`, `.venv`, `.git`, vendor folders.
3. Dry-run by default.
4. Require `--apply` to actually modify repos.
5. Print a repo-by-repo summary.

Example:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py install-all --roots "$HOME/Desktop:$HOME/projects" --dry-run
python3 ~/.claude/skills/swarm/scripts/swarm.py install-all --roots "$HOME/Desktop:$HOME/projects" --apply
```

---

## 15. Create User-Facing Commands

Make `/swarm` support these usage patterns:

```text
/swarm fix the failing tests
/swarm implement the auth middleware from issue #123
/swarm scout why the annex grouping parser fails
/swarm plan only: refactor the importer pipeline
/swarm status
/swarm doctor
/swarm install repo
/swarm install all
/swarm cleanup
```

Modes:

```text
default:
- plan → dispatch → collect → review

plan only:
- no workers launched
- produce plan and task graph only

scout:
- read-only workers only
- no edits

safe:
- max one writer
- no parallel write tasks

fast:
- prefer mini/flash
- lower confidence acceptable only for scouting
- still review before final

full:
- allow more workers
- deeper review
- run tests
```

---

## 16. MVP Milestone

If implementing all at once is too much, complete this MVP first:

```text
MVP v0.1:
- Global `/swarm` skill exists.
- `swarm.py doctor` works.
- `swarm.py install-repo` works.
- Per-repo config is created.
- One Codex executor can run a task from a prompt file.
- One opencode scout can run read-only.
- Worktree creation works.
- Logs and diff.patch are collected.
- Opus/Fable review instructions are present.
```

Then extend to:

```text
v0.2:
- multiple parallel workers
- router scoring
- automatic status dashboard
- patch application workflow
- retry loop

v0.3:
- Codex Claude Code plugin integration
- codex-rescue support if available
- Sonnet worker support
- stronger hooks
- global install-all workflow
```

---

## 17. Validation Plan

Create a disposable test repo:

```bash
mkdir -p /tmp/swarm-smoke-test
cd /tmp/swarm-smoke-test
git init
cat > calculator.py <<'PY'
def add(a, b):
    return a + b
PY
cat > test_calculator.py <<'PY'
from calculator import add

def test_add():
    assert add(1, 2) == 3
PY
git add .
git commit -m "init smoke test"
```

Then validate:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py doctor
python3 ~/.claude/skills/swarm/scripts/swarm.py install-repo /tmp/swarm-smoke-test
```

Then from Claude Code inside that repo, test:

```text
/swarm scout the calculator repo and suggest one tiny improvement
/swarm plan only: add subtract with tests
/swarm add subtract with tests
/swarm status
```

Success criteria:

```text
- Skill loads.
- Run folder created.
- Task files created.
- Worker launched or clear fallback produced.
- Logs captured.
- diff.patch captured for implementation task.
- Tests run or failure explained.
- Reviewer inspects diff before approval.
- No direct commits/pushes.
```

---

## 18. Rollout to My Repos

After smoke test passes:

1. Ask me where my repos live if not obvious.
2. Run discovery dry-run.
3. Show list of repos.
4. Ask for approval before modifying multiple repos.
5. Install per-repo config.
6. Do not alter application code.
7. Do not commit.
8. Give me a summary table:

```text
Repo | Installed | Test command detected | Notes
```

Example command:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py install-all --roots "$HOME/Desktop:$HOME/projects:$HOME/offshorly" --dry-run
```

After I approve:

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py install-all --roots "$HOME/Desktop:$HOME/projects:$HOME/offshorly" --apply
```

---

## 19. Final Deliverables

When done, report:

```text
Created:
- ~/.claude/skills/swarm/SKILL.md
- ~/.claude/skills/swarm/router.md
- ~/.claude/skills/swarm/handoff-template.md
- ~/.claude/skills/swarm/review-rubric.md
- ~/.claude/skills/swarm/scripts/swarm.py
- adapter files
- global config
- per-repo config files

Validated:
- doctor output
- smoke test result
- executor availability
- worktree creation
- log collection
- patch collection

Still needs user action:
- Codex auth, if needed
- opencode auth/config, if needed
- model name correction, if installed CLI uses different labels
- approval for install-all, if not yet approved
```

Also create:

```text
~/.claude/swarm/README.md
```

Include:

```text
How to use /swarm
How to run doctor
How to add repos
How to change executor routing
How to clean old runs
Known limitations
```

---

## 20. Do Not Do These

Do not:

* Edit unrelated project code during setup.
* Commit changes unless I explicitly ask.
* Push branches.
* Run production deployments.
* Run destructive cleanup.
* Modify secrets.
* Assume CLI flags without checking help.
* Let multiple write workers edit the same working tree.
* Claim Codex/opencode/Sonnet integration works unless tested.
* Hide failures.

Be honest about partial setup. If a piece cannot be completed because auth or CLI support is missing, create the files, document the blocker, and give me the exact next step.

Start now by inspecting the environment, then implement the global skill and runner skeleton, then smoke-test it.



## Other OpenCode Models

| Model                      | Best use in your swarm                                                                                                                                                                                                                                                        |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **DeepSeek V4 Flash Free** | Best default free worker. Use for implementation, debugging, test fixing, medium coding tasks. Probably the safest “cheap executor” choice.                                                                                                                                   |
| **North Mini Code Free**   | Best specialized coding-agent model. Good for terminal tasks, code edits, tool use, and agentic software engineering. It has a 256K context window and is explicitly optimized for code generation and terminal workflows. ([OpenRouter][1])                                  |
| **Hy3 Free**               | Good scout/planner-lite model. Use for repo exploration, reasoning, long-context investigation, and second opinions. OpenRouter describes Hy3 as a 295B MoE model built for reasoning, agentic workflows, coding, and long-horizon tasks with 256K context. ([OpenRouter][2]) |
| **Nemotron 3 Ultra Free**  | Good for huge-context planning/review/scouting. It reportedly supports up to 1M context and is described as suited for long-running agentic workflows, orchestration, coding agents, deep research, and enterprise tasks. ([OpenRouter][2])                                   |
| **MiMo V2.5 Free**         | Good experimental coding/reasoning worker. I’d test it against DeepSeek on your repos before trusting it. Xiaomi’s MiMo family is positioned around reasoning, coding, and agentic capabilities. ([arXiv][3])                                                                 |
| **Big Pickle**             | Fun wildcard / stealth model. Use for cheap second opinions, small fixes, or brainstorming. OpenCode lists it as a stealth model, currently free for limited-time feedback collection. ([OpenCode][4])                                                                        |

[1]: https://openrouter.ai/cohere/north-mini-code%3Afree "North Mini Code (free) - API Pricing & Benchmarks | OpenRouter"
[2]: https://openrouter.ai/collections/free-models "Free AI Models on OpenRouter | OpenRouter"
[3]: https://arxiv.org/abs/2601.02780?utm_source=chatgpt.com "MiMo-V2-Flash Technical Report"
[4]: https://opencode.ai/docs/zen/ "Zen | OpenCode"
