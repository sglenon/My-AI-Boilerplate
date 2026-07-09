# .swarm — My-AI-Boilerplate

Local swarm run artifacts for this repo. Subdirectories are gitignored.

- `runs/` — per-run directories with prompts, diffs, logs, status (gitignored)
- `worktrees/` — git worktrees for parallel write tasks (gitignored)

## Global Docs

Full documentation: `~/.claude/swarm/README.md`

## CLI

```bash
# Doctor check
python3 ~/.claude/skills/swarm/scripts/swarm.py doctor

# Run a task
python3 ~/.claude/skills/swarm/scripts/swarm.py run-one \
  --goal "add a subtract function with a test" \
  --executor codex \
  --repo .

# Check status
python3 ~/.claude/skills/swarm/scripts/swarm.py status --run <run_id>
```

## Config

Per-repo config: `.claude/swarm.config.json`
Global config: `~/.claude/swarm/config.json`

## Note on Test Command

No `tests/` directory was found at install time. Test command is set to empty (manual). After adding tests, update `.claude/swarm.config.json`:

```json
"test_commands": {
  "default": "uv run pytest"
}
```
