---
description: "Create Zoho Projects subtasks from the active feature's tasks.md (human-gated, safely re-runnable)"
---

# Push Tasks to Zoho

Parse the active feature's `tasks.md` and create one Zoho Projects subtask per task row. This command is human-gated — it shows you the full list of subtasks that will be created and requires explicit confirmation before calling the Zoho MCP. It is also safely re-runnable: it skips tasks whose title already exists in the target project/list.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may supply a ticket ID override or other flags.

---

## Step 1 — Resolve the active feature directory

Find the active feature directory using the same convention as other speckit-* skills:

1. Check the `SPECIFY_FEATURE_DIRECTORY` environment variable (absolute, or relative to repo root).
2. Otherwise read `.specify/feature.json` and extract the `feature_directory` key. Try parsers in this order: `jq`, then `python3`, then `grep`/`sed` as a fallback (same order as `~/.claude/skills/speckit/scripts/bash/common.sh`).
3. If neither source yields a path, report an error and stop:

   ```
   Error: No active feature found. Set SPECIFY_FEATURE_DIRECTORY or run speckit-specify first.
   ```

---

## Step 2 — Locate and parse tasks.md

Open `<feature_dir>/tasks.md`. If the file does not exist, report:

```
Error: tasks.md not found at <feature_dir>/tasks.md — run speckit-tasks first.
```

Parse task rows matching this strict format (as documented in the `speckit-tasks` skill):

```
- [ ] T### [P?] [US?] Description /path
```

Where:
- `T###` is the task number (e.g. `T001`)
- `[P?]` is the optional priority tag (e.g. `[P1]`)
- `[US?]` is the optional user story reference (e.g. `[US1]`)
- `Description` is the task description text
- `/path` is an optional file path

Only collect rows that are **unchecked** (`- [ ]`). Ignore already-checked rows (`- [x]`).

Build a list: for each matching row, the **task title** is the `T### Description` portion (include the task number prefix for traceability).

If no unchecked task rows are found, report:

```
No unchecked tasks found in tasks.md — nothing to push to Zoho.
```

and stop.

---

## Step 3 — Resolve ticket ID

Read the ticket ID from `.specify/extensions/zoho/current-ticket.json` (field: `ticket`). Try parsers in order: `jq`, then `python3`, then `grep`/`sed` fallback.

If the file does not exist or the `ticket` field is empty, ask the user:

```
No Zoho ticket found in .specify/extensions/zoho/current-ticket.json.
Please provide the Zoho ticket or task ID to file subtasks under:
```

Wait for a reply. If the user provides no ID, stop.

---

## Step 4 — Check for existing Zoho tasks (de-duplication)

Before creating anything, call `mcp__claude_ai_Zoho_Projects__get_tasks_by_project` to retrieve the existing tasks in the relevant project or task list associated with the resolved ticket ID.

Collect the titles of all existing tasks. This list is used in Step 6 to skip duplicates.

**Note**: The exact parameters required by `create_a_task` (portal ID, project ID, tasklist ID, etc.) should be checked against the live MCP tool schema at run time, as the required fields were not fully verified at authoring time. Use the project/portal context from the ticket's issue data (from `get_issue` or `get_task_details`) to resolve the correct project and task-list target.

---

## Step 5 — Show preview and require confirmation

Print the full list of subtasks that will be created, and those that will be skipped:

```
Zoho subtask push preview — Ticket <id>
────────────────────────────────────────
Will CREATE (<n> tasks):
  • T001 Description text
  • T003 Another task

Will SKIP — already exists in Zoho (<m> tasks):
  • T002 Existing task

Type "yes" or "y" to create the tasks above, or anything else to cancel.
```

Do not call `create_a_task` until the user types `yes` or `y` (case-insensitive). Any other reply — including silence, "ok", "sure", or pressing Enter — is a cancellation. On cancellation, report "Push cancelled." and stop.

---

## Step 6 — Create Zoho subtasks

Only after explicit confirmation:

For each task row in the "Will CREATE" list (i.e. whose title does not match any existing Zoho task title from Step 4):

1. Call `mcp__claude_ai_Zoho_Projects__create_a_task` with the task title and the resolved project/ticket context.
2. Record the returned Zoho task ID on success, or the error on failure.
3. Do not abort the entire run on a single failure — attempt all tasks and report individually.

---

## Step 7 — Report results

Print a summary:

```
Zoho push complete — Ticket <id>
─────────────────────────────────
Created (<n>):
  • T001 Description — Zoho task ID: <zoho-id>
  • T003 Another task — Zoho task ID: <zoho-id>

Skipped — already existed (<m>):
  • T002 Existing task

Failed (<k>):
  • T004 Some task — Error: <error message>
```

---

## Safety Rules

- Never create any Zoho task without explicit `yes`/`y` confirmation from the user (Step 5).
- Never create duplicate tasks — always check existing task titles before creating (Step 4 + Step 6).
- Never push already-checked (`- [x]`) rows from tasks.md.
- Never push, force-push, amend git history, or modify `.specify/` files beyond reading `feature.json` and `extensions/zoho/current-ticket.json`.
- If `create_a_task` required parameters are unclear from the live MCP schema at run time, report the ambiguity to the user rather than guessing silently.
