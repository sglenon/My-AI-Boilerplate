---
name: speckit
description: Spec-Driven Development (SDD) toolkit — overview, routing table, template resolution stack, and hook lifecycle reference. Run speckit-init to set up a project. See individual speckit-<command> skills for each stage.
---

# speckit — Spec-Driven Development Toolkit

Global library host for the spec-kit SDD workflow. This skill is a reference/router only — it performs no file operations itself.

For project setup or registering presets/extensions, run the `speckit-init` skill.

See `~/.claude/skills/speckit/conventions.md` for `.specify/` layout, feature.json, numbering rules, and composed-template resolution contract.

---

## 7-Stage Pipeline

```
constitution → specify → clarify → plan → tasks → [analyze] → implement
                                                              ↓
                                                        checklist (optional, parallel with analyze/implement)
```

| Intent | Skill |
|--------|-------|
| Create or update the project constitution | `speckit-constitution` |
| Write a new feature spec | `speckit-specify` |
| Clarify underspecified areas in the spec | `speckit-clarify` |
| Produce the implementation plan and design artifacts | `speckit-plan` |
| Generate a dependency-ordered tasks.md | `speckit-tasks` |
| Cross-artifact consistency analysis (read-only) | `speckit-analyze` |
| Execute the tasks phase by phase | `speckit-implement` |
| Generate requirements-quality checklist | `speckit-checklist` |
| Initialize .specify/ or register presets/extensions | `speckit-init` |

---

## Template Resolution Stack

When any command resolves a template (e.g. `spec-template`, `plan-template`), the resolver applies these layers in order — first match wins per section:

```
override  (project-local .specify/templates/<name>.md)
  ↓
presets   (each registered preset in priority order, highest first)
  ↓
extensions (each installed extension in registration order)
  ↓
core      (built-in template at ~/.claude/skills/speckit/templates/<name>.md)
```

Composition strategies applied per layer:

- **replace** — the layer's content replaces the entire section
- **prepend** — the layer's content is inserted before the section body
- **append** — the layer's content is inserted after the section body
- **wrap** — the layer wraps the section with a header block and footer block

Scripts resolve all layers before handing `TEMPLATE_CONTENT` to the agent — the agent never sees raw individual layers, only the composed result.

---

## Hook Lifecycle

Each core command checks `.specify/extensions.yml` at two points: **before** its main work and **after** it completes.

Hook events (before/after pairs):

```
before_constitution / after_constitution
before_specify      / after_specify
before_clarify      / after_clarify
before_plan         / after_plan
before_tasks        / after_tasks
before_analyze      / after_analyze
before_implement    / after_implement
before_checklist    / after_checklist
```

For each executable hook, behavior depends on `optional`:

- `optional: true` — the skill surfaces an **Optional Hook** notice; user decides whether to run it
- `optional: false` — the skill surfaces an **Automatic Hook** notice, invokes `speckit-<command>` (the matching installed skill), and waits for it to finish before proceeding

Hooks with `enabled: false` are silently skipped. Hooks with a non-empty `condition` field are skipped at the skill level (condition evaluation belongs to the HookExecutor runtime). If `.specify/extensions.yml` is absent or unparseable, all hook checks are silently skipped.

---

## First-Time Setup

Run `speckit-init` in your project directory. It scaffolds `.specify/`, writes `init-options.json` (with `ai_skills: true` and `ai: "claude"` for skills-mode hook rendering), and writes `integration.json`. Then optionally register a preset or extension.
