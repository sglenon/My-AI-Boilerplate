# Claude Code Orchestration

Baseline setup for routing tasks across specialized Claude agents. Master agent plans & reviews. Worker agent implements. Main thread dispatches.

## Why

Splits labor by capability:
- **Planning & review** → high-reasoning model (Opus)
- **Implementation** → faster model (Sonnet)
- **User** → never types `@master` or `@worker`; delegation automatic

Improves outcomes (stronger model reviews) + reduces cost (expensive model used only where reasoning matters).

## Quick Start

Project lives in `claude-orchestration/` directory. Contains:

- `.claude/agents/master.md` — high-reasoning agent definition
- `.claude/agents/worker.md` — implementation agent definition
- `.claude/settings.json` — routing configuration
- `CLAUDE.md` — delegation rules (what agent does what)
- `ORCHESTRATION_GUIDE.md` — detailed explanation of pattern
- `WORKSPACE_TEMPLATE.md` — template for applying to new projects

## How It Works

### Typical Flow

1. User requests task → main thread receives it
2. Main thread routes to `master` (if multi-step/uncertain) or `worker` (if clear/scoped)
3. Master plans (never writes code). Worker implements (never approves own work).
4. Master reviews worker's output. If issues found → sends to worker for fixes. Loop until APPROVED.
5. User gets final result.

### Agent Roles

| Agent  | Model               | Does                                  | Does NOT        |
|--------|---------------------|---------------------------------------|-----------------|
| master | claude-opus-4-8     | Plan, review, debug, decide, diagnose | Write code      |
| worker | claude-sonnet-4-6   | Write, edit, fix, implement, test     | Approve own work |

Tool asymmetry enforces roles:
- Master: Read, Glob, Grep, Bash (no Edit/Write)
- Worker: Read, Edit, Write, Bash (has file-mutation tools)

### Routing Rules

Key rules from `CLAUDE.md`:

- **Multi-step work** → master plans first; worker implements; master reviews
- **Clear, scoped changes** → straight to worker
- **Debugging/investigation** → master diagnoses root cause
- **Docs/CLAUDE.md changes** → worker writes (mechanical prose), master decides new structure (architectural spine)
- **Trivial edits** → worker
- Uncertain which? → default to master

Master never writes code. Worker never approves. Main thread dispatches.

## File Structure

```
claude-orchestration/
├── CLAUDE.md                          # Delegation rules
├── ORCHESTRATION_GUIDE.md             # Detailed explanation
├── WORKSPACE_TEMPLATE.md              # Template for new projects
├── .claude/
│   ├── agents/
│   │   ├── master.md                  # Master agent (plans, reviews)
│   │   └── worker.md                  # Worker agent (implements)
│   ├── settings.json                  # Configuration
│   ├── settings.local.json            # Local overrides
│   └── scripts/
│       └── parse_usage.py             # Token tracking script
└── TOKEN_TRACKING_PLAN.md             # Token usage documentation
```

## Using This Template

To apply orchestration to your own project:

1. Copy `CLAUDE.md` to your project root
2. Copy `.claude/agents/master.md` and `.claude/agents/worker.md`
3. Update `.claude/settings.json` with agent references
4. Adjust routing rules in CLAUDE.md for your use case
5. See `WORKSPACE_TEMPLATE.md` for step-by-step guide

## Key Concepts

**Delegation**: Main thread never does substantive work. Routes to agents based on task type.

**Division of labor**: Planning/review uses strong model. Implementation uses faster model.

**Tool asymmetry**: Master has no write tools. Worker has write tools. Enforces "who does what" at tool level.

**Review loop**: Master approves before work is done. If issues found, worker fixes without asking human for input.

**Decision Points**: Multi-step changes surface what needs human approval before implementation starts.

## Documentation

- `ORCHESTRATION_GUIDE.md` — full explanation with examples
- `CLAUDE.md` — delegation rules and routing logic
- `WORKSPACE_TEMPLATE.md` — instructions to replicate for your project

## Next Steps

1. Read `ORCHESTRATION_GUIDE.md` for detailed walkthrough
2. Review agent definitions in `.claude/agents/`
3. See `CLAUDE.md` routing rules to understand when each agent activates
4. Apply to your project using `WORKSPACE_TEMPLATE.md`

---

## Swarm Setup

`/swarm` extends the master/worker pattern to a multi-executor orchestration system. The existing `master` agent is the planner/reviewer. The existing `worker` agent (or `claude -p`) is the sonnet executor. External executors (codex, opencode) add cheaper/faster implementation capacity.

### Prerequisites (verified tool versions)

| Tool | Verified version | Notes |
|---|---|---|
| git | 2.43.0 | Required |
| python3 | 3.12.3 | Required |
| node | v22.22.3 | Optional (for JS repos) |
| claude CLI | 2.1.205 | At `~/.local/bin/claude`; `-p` flag for non-interactive |
| codex CLI | installed | `codex exec -m gpt-5.5` for non-interactive; real model = gpt-5.5 |
| opencode CLI | 1.17.16 | `opencode run -m opencode/deepseek-v4-flash-free "..." --format json` |
| tmux | NOT installed | swarm uses subprocess only; tmux not used |
| uv | 0.11.19 | For Python project management |

### Install Steps

**1. Verify global swarm skill exists:**

```bash
ls ~/.claude/skills/swarm/SKILL.md
```

**2. Run doctor to check all tools:**

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py doctor
```

**3. Install swarm config for a repo:**

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py install-repo /path/to/repo
```

This creates `.claude/swarm.config.json`, `.swarm/README.md`, and updates `.gitignore`.

**4. Run a task:**

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py run-one \
  --goal "add a subtract function with a test" \
  --executor codex \
  --repo /path/to/repo
```

**5. Check status:**

```bash
python3 ~/.claude/skills/swarm/scripts/swarm.py status --run <run_id>
```

### How /swarm Relates to master/worker

The existing master/worker pattern (in `claude-orchestration/`) is the foundation. Swarm extends it:

| Role | master/worker | swarm |
|---|---|---|
| Planner | master agent (Opus) | same master agent |
| Reviewer | master agent | same master agent |
| Implementer | worker agent (Sonnet) | worker agent OR codex exec OR opencode |
| Routing | CLAUDE.md rules | swarm router.md + config.json |
| Isolation | session context | git worktrees per task |
| Artifacts | Claude session | run dir with diffs/logs/status |

Swarm does not replace master/worker. It adds external executor delegation + worktree isolation + structured artifact collection.

### Known Limitations

- **tmux**: Not installed. Subprocess only. This is expected and non-breaking.
- **Model names**: `codex-5.4-mini` and `codex-5.4` from PLAN.md are not real model identifiers. Real model is `gpt-5.5`. The PLAN.md labels are disabled config aliases only.
- **install-all**: Dry-run only in v0.1. Lists repos but won't write to them without `--apply`, which requires separate explicit approval.
- **Sonnet non-interactive**: `claude -p` starts a fresh session. Falls back to manual prompt if invocation fails.
- **No auto-merge**: Every diff requires master review and explicit human approval for destructive actions.

### Global Config

`~/.claude/swarm/config.json` — executor routing, parallelism, protected globs.

### Per-Repo Config

`.claude/swarm.config.json` — test commands, protected paths, preferred executors.

### Full Docs

`~/.claude/swarm/README.md` — complete usage guide including how to clean runs, change routing, and known limitations.
