---
name: speckit-init
description: Initialize .specify/ in a project, or register/unregister presets and extensions. Lists available presets and extensions from the global catalog. Writes init-options.json (ai_skills=true, ai=claude) and integration.json for skills-mode hook rendering. Idempotent — never clobbers an existing constitution.md, spec, or already-registered preset/extension.
---

## User Input

```text
$ARGUMENTS
```

Parse the arguments to determine the action:
- No arguments or `init` → scaffold `.specify/` if not present; print available presets/extensions
- `preset add <id> [--priority N]` → register a preset
- `preset remove <id>` → unregister a preset
- `extension add <id>` → register an extension
- `extension remove <id>` → unregister an extension
- `list` → list registered presets and extensions

---

## Action: Init / Scaffold `.specify/`

If `<project>/.specify/` does not exist, create the directory tree and write config files:

### Step 1 — Create directory tree

```bash
mkdir -p .specify/memory
mkdir -p .specify/templates
mkdir -p .specify/presets
mkdir -p .specify/extensions
mkdir -p specs
```

### Step 2 — Copy core templates

Copy the 5 core templates from `~/.claude/skills/speckit/templates/` into `.specify/templates/`:

```bash
cp ~/.claude/skills/speckit/templates/spec-template.md .specify/templates/
cp ~/.claude/skills/speckit/templates/plan-template.md .specify/templates/
cp ~/.claude/skills/speckit/templates/tasks-template.md .specify/templates/
cp ~/.claude/skills/speckit/templates/constitution-template.md .specify/templates/
cp ~/.claude/skills/speckit/templates/checklist-template.md .specify/templates/
```

### Step 3 — Write `init-options.json`

Write `.specify/init-options.json` with skills-mode settings for Claude Code:

```json
{
  "ai": "claude",
  "ai_skills": true,
  "feature_numbering": "sequential"
}
```

Explanation of key fields:
- `"ai": "claude"` — selects the Claude Code agent key (a member of `CONDITIONAL_SLASH_AGENTS` in the spec-kit invocation-style registry)
- `"ai_skills": true` — enables skills mode, so hook rendering uses `/speckit-<name>` invocations rather than CLI slash commands
- `"feature_numbering": "sequential"` — default sequential NNN numbering; change to `"timestamp"` if the user prefers timestamp-based prefixes

### Step 4 — Write `integration.json`

Write `.specify/integration.json` with the installed integration state:

```json
{
  "version": "1.0.0",
  "integration_state_schema": 1,
  "integration": "claude",
  "default_integration": "claude",
  "installed_integrations": ["claude"],
  "integration_settings": {
    "claude": {
      "invoke_separator": "-"
    }
  }
}
```

The `invoke_separator: "-"` field ensures `get_invoke_separator` returns `-` for the claude integration, so any rendered command hint shows `/speckit-plan` instead of `/speckit.plan`.

### Step 5 — Create preset registry

Write `.specify/presets/.registry` as a JSON file (the resolver parses it with `json.loads`):

```json
{"presets": {}}
```

The resolver expects shape `{"presets": {"<id>": {"enabled": bool, "priority": int}}}`. An empty `{"presets": {}}` is valid and means no presets are registered yet.

### Step 6 — Print available presets and extensions

Read `~/.claude/skills/speckit/presets/catalog.json` and `~/.claude/skills/speckit/extensions/catalog.json` and print a summary:

```
Available presets (register with: speckit-init preset add <id>):
  lean              — Minimal, opinionated spec workflow for small teams
  constitution-sync — Auto-syncs constitution changes to downstream templates
  scaffold          — Project scaffolding preset
  self-test         — Self-test preset

Available extensions (register with: speckit-init extension add <id>):
  git               — Git workflow hooks (branch creation, commits)
  assess            — Assessment and discovery workflow
  bug               — Bug investigation and fix workflow
  agent-context     — Agent context management
  template          — Custom template management
```

(Read actual names and descriptions from the catalog files — do not hard-code the list above.)

If `.specify/` already exists, skip scaffold steps and print what is already installed (presets, extensions from `.registry` and `extensions.yml`).

---

## Action: `preset add <id> [--priority N]`

1. Verify `<id>` exists in `~/.claude/skills/speckit/presets/catalog.json` (or as a directory under `~/.claude/skills/speckit/presets/<id>/`). If not found, halt with an error.
2. Check if `<project>/.specify/presets/<id>/` already exists. If so, print "Preset '<id>' is already registered." and stop (idempotent).
3. Copy `~/.claude/skills/speckit/presets/<id>/` → `<project>/.specify/presets/<id>/`
4. Update `<project>/.specify/presets/.registry` (JSON format):
   - Read the current JSON (parse with `json.loads`; if absent or invalid, start with `{"presets": {}}`)
   - Insert key `"<id>": {"enabled": true, "priority": N}` under `presets` (default priority `10` if unspecified)
   - Write the updated JSON back (pretty-printed, `json.dumps(..., indent=2)`)
5. Print confirmation: "Registered preset '<id>' with priority <priority>."

---

## Action: `preset remove <id>`

1. Check if `<project>/.specify/presets/<id>/` exists. If not, print "Preset '<id>' is not registered." and stop.
2. Remove the directory: `rm -rf .specify/presets/<id>/`
3. Update `<project>/.specify/presets/.registry` (JSON format):
   - Read and parse the JSON
   - Delete the key `"<id>"` from the `presets` object
   - Write the updated JSON back
4. Print confirmation: "Unregistered preset '<id>'."

---

## Action: `extension add <id>`

1. Verify `<id>` exists in `~/.claude/skills/speckit/extensions/catalog.json` (or as a directory under `~/.claude/skills/speckit/extensions/<id>/`). If not found, halt with an error.
2. Check if `<project>/.specify/extensions/<id>/` already exists. If so, print "Extension '<id>' is already registered." and stop (idempotent).
3. Copy `~/.claude/skills/speckit/extensions/<id>/` → `<project>/.specify/extensions/<id>/`
4. Read the extension's `extension.yml` from the copied location. Aggregate its hooks into `<project>/.specify/extensions.yml`:
   - If `extensions.yml` does not exist, create it with this structure:
     ```yaml
     installed:
       - <id>
     hooks:
       # hooks from extension.yml merged here by event name
     settings:
       auto_execute_hooks: true
     ```
   - If `extensions.yml` already exists, append `<id>` to the `installed:` list and merge hook entries under the appropriate event keys (e.g., `hooks.before_specify:`, `hooks.after_specify:`, etc.)
   - For each hook entry, preserve all fields: `extension`, `command`, `description`, `prompt`, `optional`, `enabled`, `condition` (if present)
5. **Materialize extension command skills**: For each `commands/*.md` file in the extension directory, create a global skill at `~/.claude/skills/speckit-<id>-<cmd>/SKILL.md`:
   - Parse the command filename to derive `<cmd>` (e.g., `speckit.git.commit.md` → `git-commit`, so skill = `speckit-git-commit`)
   - Translate the command prompt the same way as the 8 core skills:
     - `$ARGUMENTS` → the skill's own args
     - `__SPECKIT_COMMAND_X__` / references to other commands → "the `speckit-x` skill"
     - Script references → absolute paths under `~/.claude/skills/speckit/scripts/bash/`
     - `handoffs:` / auto-chaining → a plain trailing "Next: run `speckit-<x>`" line
     - Pre/post hook blocks → translated to plain instructions (same hook logic as the 8 core skills)
   - Write valid SKILL.md frontmatter: `name: speckit-<id>-<cmd>` and `description:` derived from the command's `description:` frontmatter field
6. Print confirmation: "Registered extension '<id>'. Materialized <N> command skill(s): speckit-<id>-<cmd>, ..."

---

## Action: `extension remove <id>`

1. Check if `<project>/.specify/extensions/<id>/` exists. If not, print "Extension '<id>' is not registered." and stop.
2. Remove the project-local copy: `rm -rf .specify/extensions/<id>/`
3. Remove `<id>` from the `installed:` list in `<project>/.specify/extensions.yml`. Remove its hook entries from under each event key. If `installed:` becomes empty, leave `extensions.yml` in place (with empty `installed: []`).
4. Remove the materialized global skill directories: `rm -rf ~/.claude/skills/speckit-<id>-*/` (all skills whose name starts with `speckit-<id>-`).
5. Print confirmation: "Unregistered extension '<id>'. Removed <N> command skill(s)."

---

## Action: `list`

Print what is currently registered in this project:

1. Read `<project>/.specify/presets/.registry` and list each preset with its priority.
2. Read `<project>/.specify/extensions.yml` and list each extension from the `installed:` key.
3. List any materialized extension command skills found under `~/.claude/skills/speckit-*` (exclude the 8 core skills and `speckit-init`).

---

## Safety Rules

- Never overwrite `.specify/memory/constitution.md` — if it exists and action is init, leave it intact.
- Never overwrite an existing spec file under `specs/`.
- Never re-register a preset or extension that is already registered (idempotent check first).
- Never remove the core skill directories (`speckit-constitution`, `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement`, `speckit-checklist`, `speckit-init`, `speckit`).
- Do not copy PowerShell scripts (`.ps1`) when registering extensions.
