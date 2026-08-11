# AI-Guided V2 Installation

This document is the authoritative installation procedure for the AI Excellence
Playbook v2 orchestration package. An AI assistant reads these instructions and
installs `orchestration/core/` into a target project.

V2 is a new installation. This procedure does not upgrade an earlier
slash-command orchestration workflow.

---

## How to Invoke

From a session that can read this playbook and the target project, ask:

```
Read orchestration/INSTALL.md and install AI Excellence Playbook v2 into:
<absolute-target-project-path>
```

The target path is required. Do not infer a different repository when the
request is ambiguous.

---

## Installer Role

When following this document, you are the V2 Installation Agent.

Your responsibilities are:

1. Resolve and validate the source and target paths.
2. Inspect the target without changing it.
3. Check prerequisites.
4. Classify every installation operation.
5. Present the plan and conflicts before writing.
6. Apply only approved changes.
7. Validate the completed installation.
8. Return the required installation report.

Do not perform feature work, refactoring, Git operations, dependency upgrades,
or unrelated cleanup.

---

## Safety Rules

Always follow these rules:

- Use absolute paths for source, target, and reported files.
- Keep the playbook source and target project separate.
- Never install into `orchestration/core/` itself.
- Never stage, commit, branch, push, reset, clean, or discard Git changes.
- Never replace an existing non-identical file without explicit approval.
- Never replace an entire merge-owned configuration file.
- Never remove existing project instructions, hooks, ignore rules, or
  attributes.
- Never request, display, log, or commit a Sonar token.
- Never copy local settings, generated usage data, bootstrap markers, caches,
  or scanner output.
- Stop when a conflict requires project-specific judgment.

---

## Source and Target

### Source

Locate the playbook root by confirming these files exist:

```
orchestration/core/CLAUDE.md
orchestration/core/.claude/settings.json
orchestration/core/.claude/agents/master.md
orchestration/core/.claude/agents/worker.md
orchestration/core/.claude/agents/commit.md
orchestration/core/.claude/agents/sonar.md
```

Set `<source>` to the absolute path of `orchestration/core/`.

### Target

Resolve the user-provided target to an absolute path and confirm:

- The directory exists.
- It is not the playbook's `orchestration/core/` directory.
- The current user can read and write it.
- It is running under Linux, WSL2, or macOS with Bash available.

Native Windows shells are outside the supported v2 installation contract.

---

## Phase 1: Read-Only Inventory

Before writing anything, inspect:

```
<target>/CLAUDE.md
<target>/.claude/settings.json
<target>/.claude/agents/
<target>/.claude/hooks/
<target>/.claude/scripts/
<target>/.gitignore
<target>/.claude/.gitignore
<target>/.gitattributes
<target>/ORCHESTRATION_GUIDE.md
<target>/WORKSPACE_TEMPLATE.md
<target>/sonarqube/
```

Also check for conflicting previous workflows:

```
<target>/.claude/commands/orchestrate.md
<target>/.claude/commands/installer.md
```

If either legacy command exists, report it and stop before writing. V2 does not
remove or upgrade previous orchestration installations.

Classify each required target as:

- `CREATE` — target does not exist.
- `IDENTICAL` — target exists and matches the source.
- `MERGE` — configuration exists and can preserve both source and target data.
- `CONFLICT` — non-identical owned file requires replace/skip approval.
- `SKIP` — reference-only or explicitly excluded.

---

## Phase 2: Prerequisite Check

Run non-mutating version and availability checks:

```
claude --version
bash --version
python3 --version
node --version
npm --version
jq --version
docker --version
docker compose version
npm ls -g --depth=0 @juliusbrussee/caveman-code
npm ls -g --depth=0 diffwarden
```

Requirements:

| Dependency | Requirement |
|---|---|
| Claude Code | CLI available with agent-team support |
| Bash | Available in Linux, WSL2, or macOS |
| Python | 3.10 or later |
| Node.js/npm | Available |
| `jq` | Available |
| Docker | Available |
| Docker Compose | V2 available |
| Caveman | Global npm package available |
| Diffwarden | Global npm package available |

Do not install missing dependencies during the read-only phase. Report exact
missing prerequisites and the commands documented by
`core/.claude/hooks/bootstrap.sh`.

Files may be installed with missing prerequisites only after the user approves
continuing. The final status must remain `PARTIAL` until every prerequisite is
available.

---

## Phase 3: Build the Installation Plan

Present:

1. Source and target absolute paths.
2. Platform and prerequisite results.
3. Every `CREATE`, `IDENTICAL`, `MERGE`, `CONFLICT`, and `SKIP` operation.
4. Exact merge behavior for configuration files.
5. Missing prerequisites and manual Sonar setup.

Wait for approval before writing.

For each `CONFLICT`, ask the user to choose:

- `replace` — back up the target, then install the source.
- `skip` — leave the target unchanged and report a partial installation.
- `abort` — stop without applying remaining changes.

Do not apply one conflict choice automatically to every file unless the user
explicitly requests that behavior.

---

## Phase 4: Apply Files

Apply the ignore-file merges before creating backups or copying runtime files.

### Copy with conflict checking

Create missing parent directories and install:

```
ORCHESTRATION_GUIDE.md
WORKSPACE_TEMPLATE.md
.claude/agents/master.md
.claude/agents/worker.md
.claude/agents/commit.md
.claude/agents/sonar.md
.claude/hooks/bootstrap.sh
.claude/hooks/session_start.sh
.claude/hooks/session_end.sh
.claude/scripts/parse_usage.py
.claude/scripts/sonar_scan.sh
sonarqube/docker-compose.yml
sonarqube/INSTALL.md
```

For each path:

- Copy when missing.
- Skip when identical.
- Treat non-identical content as a conflict.
- Before an approved replacement, copy the original to:

  ```
  <target>/.claude/backups/v2-install/<timestamp>/<relative-target-path>
  ```

- Preserve the target's relative path inside the backup directory.
- Never overwrite an existing backup.

### Merge `CLAUDE.md`

If the target has no `CLAUDE.md`, copy the source file.

If it exists:

1. Preserve all project-specific content.
2. Check for an existing v2 orchestration block.
3. Insert or replace exactly one block using these markers:

```
<!-- AI-EXCELLENCE-V2:START -->
<!-- AI-EXCELLENCE-V2:END -->
```

4. Use the source `CLAUDE.md` content inside the block, changing its first
   `# CLAUDE.md` heading to `## AI Excellence V2 Orchestration`.
5. Do not duplicate the block on repeated installation.
6. If existing instructions conflict with automatic delegation or agent
   ownership, classify the file as `CONFLICT` and ask for direction.

### Merge `.claude/settings.json`

If missing, copy the source settings.

If it exists:

1. Parse it as JSON. Stop if invalid.
2. Preserve every unrelated top-level key.
3. Merge this environment value:

```json
{
  "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
}
```

4. Preserve existing environment values.
5. Add the source `SessionStart` and `SessionEnd` hook entries.
6. Preserve other hooks under those events.
7. Deduplicate hooks by exact command string.
8. If the same environment key has a different value, classify it as a
   `CONFLICT`.
9. Write valid, consistently indented JSON.

### Merge `.gitignore`

Do not copy the source `.gitignore` wholesale. Preserve the target and add only
missing orchestration-specific entries:

```
.claude/usage.csv
.claude/.parsed_sessions.json
.claude/sonar.env
.claude/settings.local.json
.claude/backups/
.scannerwork/
```

Do not add unrelated Python, IDE, environment, dependency, or operating-system
patterns from the source template.

### Merge `.claude/.gitignore`

Preserve existing entries and add:

```
.bootstrap_done
```

### Merge `.gitattributes`

Preserve existing entries and add only missing rules:

```
*.sh text eol=lf
*.py text eol=lf
```

### Reference-only file

Do not install this file unless the user explicitly asks for design history:

```
.claude/TOKEN_TRACKING_PLAN.md
```

### Never copy or generate

```
.claude/settings.local.json
.claude/sonar.env
.claude/usage.csv
.claude/.parsed_sessions.json
.claude/.bootstrap_done
.claude/backups/
.claude/scripts/__pycache__/
.scannerwork/
```

Do not ask the user to paste a Sonar token into chat. Direct them to
`sonarqube/INSTALL.md` to create `.claude/sonar.env` locally.

### Permissions

Make runtime shell files executable:

```
chmod +x <target>/.claude/hooks/*.sh
chmod +x <target>/.claude/scripts/*.sh
```

---

## Phase 5: Validate

Run these checks from the target project.

### Required paths

Confirm every non-reference file in the copy list exists.

### Settings

```
python3 -m json.tool .claude/settings.json
```

Confirm:

- Agent-team environment value is `1`.
- SessionStart appears once.
- SessionEnd appears once.
- Existing unrelated settings remain.

### Shell syntax

```
bash -n .claude/hooks/bootstrap.sh
bash -n .claude/hooks/session_start.sh
bash -n .claude/hooks/session_end.sh
bash -n .claude/scripts/sonar_scan.sh
```

### Python parser

```
python3 .claude/scripts/parse_usage.py --help
```

### SonarQube configuration

```
docker compose -f sonarqube/docker-compose.yml config --quiet
```

Do not start containers unless the user explicitly requests it.

Confirm `.claude/sonar.env` exists without reading or printing its contents. If
it is absent, record the installation as `PARTIAL` and direct the user to
`sonarqube/INSTALL.md`.

### Ignore protection

When the target is a Git repository, confirm these paths are ignored:

```
git check-ignore .claude/sonar.env
git check-ignore .claude/usage.csv
git check-ignore .claude/.parsed_sessions.json
git check-ignore .claude/settings.local.json
git check-ignore .scannerwork/
```

### Core consistency

Confirm:

- Master uses `claude-opus-4-8`.
- Worker, commit, and sonar use `claude-sonnet-5`.
- Master and sonar lack write tools.
- Worker has write tools.
- No distributed setting references a local status-line command, `/tmp` debug
  file, absolute machine path, or `settings.local.json`.
- `CLAUDE.md` references `ORCHESTRATION_GUIDE.md` and
  `WORKSPACE_TEMPLATE.md`, and both files exist.

Do not run the bootstrap hook during installation without explicit approval
because it may install system or global npm dependencies.

---

## Phase 6: Report

Return exactly these sections:

```
## Installation Status
COMPLETE | PARTIAL | BLOCKED

## Target
<absolute target path>

## Prerequisites
- <dependency>: PASS | MISSING | UNSUPPORTED

## Created
- <absolute path>

## Merged
- <absolute path>: <what was preserved and added>

## Replaced
- <absolute path>: <backup path>

## Skipped
- <absolute path>: <reason>

## Validation
- <check>: PASS | FAIL

## Manual Steps
- <remaining user action>
```

Status definitions:

- `COMPLETE` — every required file and prerequisite is present,
  `.claude/sonar.env` exists, and all validation checks pass.
- `PARTIAL` — files were installed, but a prerequisite, conflict, skipped file,
  or validation item remains.
- `BLOCKED` — installation could not proceed safely.

Never report `COMPLETE` when a required core file is missing or a validation
check failed.

---

## Expected Manual Follow-Up

After a complete file installation:

1. Follow `sonarqube/INSTALL.md`.
2. Create `.claude/sonar.env` locally without sharing the token in chat.
3. Start SonarQube when ready.
4. Restart Claude Code so project agents and settings reload.
5. Run the orchestration test in `WORKSPACE_TEMPLATE.md`.
