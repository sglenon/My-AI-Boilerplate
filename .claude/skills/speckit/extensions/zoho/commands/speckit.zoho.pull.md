---
description: "Pull ticket title and description from Zoho Projects to seed speckit-specify"
---

# Pull Zoho Ticket

Fetch a Zoho Projects ticket or task and emit its title and description so they can feed directly into the `speckit-specify` skill. This command is entirely optional — you can skip it and paste a feature description manually into `speckit-specify` instead.

## User Input

```text
$ARGUMENTS
```

The argument is a Zoho ticket or task ID (required). If `$ARGUMENTS` is empty, ask the user:

```
Please provide the Zoho ticket or task ID to pull (e.g. PROJ-123 or a numeric task ID):
```

Wait for the reply. If the user provides no ID, stop and report that the pull was skipped.

---

## Step 1 — Fetch from Zoho Projects MCP

This command is read-only against Zoho. It never creates or modifies any Zoho data.

Try `mcp__claude_ai_Zoho_Projects__get_issue` first, passing the ticket ID as the issue identifier. If that call fails or returns no result (e.g. the ID identifies a task rather than an issue), fall back to `mcp__claude_ai_Zoho_Projects__get_task_details` with the same ID.

Extract:
- **Title**: the issue/task subject or title field
- **Description**: the issue/task description or body field

If both calls fail or return no usable content, report the error and stop. Do not proceed to Step 2 with empty data.

---

## Step 2 — Write current-ticket.json

Write `.specify/extensions/zoho/current-ticket.json` in the current project (`.specify/` at the repo root, relative to wherever the user is running this command). Create the directory `.specify/extensions/zoho/` if it does not already exist.

Contents:

```json
{"ticket": "<id>"}
```

Where `<id>` is the exact ticket/task ID provided by the user. This file is read later by the `speckit-commit` skill (which checks for it defensively and skips if absent) and by the `speckit-zoho-push-tasks` skill.

---

## Step 3 — Emit feature description

Print the pulled title and description in a clear block so the user can review it:

```
Pulled from Zoho — Ticket <id>
─────────────────────────────
Title:       <title>
Description:
<description text>
─────────────────────────────
```

---

## Step 4 — Hand off to speckit-specify

End with:

```
Next: run `speckit-specify` — pass the description above as the feature description.
```

The user can copy the pulled description and provide it as input to `speckit-specify`, exactly as they would with a manually written description.

---

## Optional Workflow Note

This command is entirely optional. If you already have a feature description, you can skip this command and run `speckit-specify` directly by pasting the description yourself.
