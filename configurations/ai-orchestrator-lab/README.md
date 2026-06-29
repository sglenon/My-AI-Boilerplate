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
