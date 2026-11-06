# Zoho Projects Extension for Spec Kit

Integrates Zoho Projects into the Spec Kit spec-driven-development workflow. Provides two commands:

- **`speckit-zoho-pull`** — fetch a Zoho ticket's title and description before writing the spec.
- **`speckit-zoho-push-tasks`** — create Zoho subtasks from the feature's `tasks.md` after task generation.

Both commands are optional and human-gated. Neither runs silently or makes Zoho writes without explicit confirmation.

---

## Commands

### `speckit-zoho-pull`

Pull a Zoho ticket or task by ID, emit its title and description, write `.specify/extensions/zoho/current-ticket.json` with the ticket ID, and prompt you to run `speckit-specify` next.

- Read-only against Zoho (no writes).
- Entirely optional — skip it and paste a description manually into `speckit-specify` if you prefer.

### `speckit-zoho-push-tasks`

Parse the active feature's `tasks.md` for unchecked task rows, show a preview, and (after explicit `yes`/`y` confirmation) create one Zoho subtask per row via the Zoho Projects MCP.

- Safely re-runnable — skips tasks whose title already exists in Zoho, so partial failures do not create duplicates.
- Never creates any task without explicit user confirmation.

---

## Hooks

| Hook | Command | Optional | Prompt |
|------|---------|----------|--------|
| `before_specify` | `speckit.zoho.pull` | Yes | "Pull ticket description from Zoho before writing the spec?" |
| `after_tasks` | `speckit.zoho.push-tasks` | Yes | "Create Zoho subtasks from tasks.md for this ticket?" |

Both hooks are optional. If you decline (or if no ticket ID is available), the core workflow continues normally.

---

## Dependencies

This extension depends on the **Zoho Projects MCP** being connected and active in the current Claude Code session. No additional script installation is required — the MCP tools are invoked directly.

Required MCP tools:
- `mcp__claude_ai_Zoho_Projects__get_issue`
- `mcp__claude_ai_Zoho_Projects__get_task_details`
- `mcp__claude_ai_Zoho_Projects__create_a_task`
- `mcp__claude_ai_Zoho_Projects__get_tasks_by_project`

---

## Configuration

After installation, edit `.specify/extensions/zoho/zoho-config.yml` to set optional defaults:

```yaml
default_portal: ""      # Zoho portal slug/ID
default_project: ""     # Zoho project ID
default_tasklist: ""    # Task list name for subtasks
auto_push_after_tasks: false   # Always false — opt-in only
```

`auto_push_after_tasks` must remain `false`. Setting it to `true` only enables the after-tasks hook prompt — the `speckit-zoho-push-tasks` skill still always requires explicit `yes`/`y` before creating any Zoho task.
