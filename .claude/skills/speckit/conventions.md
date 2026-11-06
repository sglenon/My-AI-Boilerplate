# spec-kit Conventions

Shared reference for the `.specify/` layout, `feature.json` mechanism, spec numbering, and composed-template resolution contract. Referenced by all `speckit-*` command skills.

---

## `.specify/` Directory Layout

```
<project-root>/
├── .specify/
│   ├── init-options.json          # Init settings: ai, ai_skills, feature_numbering, etc.
│   ├── integration.json           # Installed integrations state
│   ├── feature.json               # Active feature pointer (written by speckit-specify)
│   ├── memory/
│   │   └── constitution.md        # Project constitution (written by speckit-constitution)
│   ├── templates/                 # Project-local template overrides (highest priority layer)
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   ├── tasks-template.md
│   │   ├── constitution-template.md
│   │   └── checklist-template.md
│   ├── presets/
│   │   ├── .registry              # Registered presets with priority values
│   │   └── <preset-id>/           # Copied preset contents
│   └── extensions/
│       └── <extension-id>/        # Copied extension contents
├── extensions.yml                 # Aggregated hook registrations for all installed extensions
└── specs/
    └── NNN-<slug>/                # Feature directories
        ├── spec.md
        ├── plan.md
        ├── tasks.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md
        ├── contracts/
        └── checklists/
```

---

## `feature.json` Mechanism

`speckit-specify` writes `.specify/feature.json` after creating a feature directory:

```json
{
  "feature_directory": "specs/003-user-auth"
}
```

Downstream commands (`speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement`, `speckit-checklist`) read this file to locate the active feature directory without relying on branch name conventions.

---

## `specs/NNN-<slug>/` Numbering Rule

Feature directories follow zero-padded 3-digit sequential numbering by default:

- Scan existing `specs/` subdirectories for the highest NNN prefix
- Next directory = `NNN+1-<slug>` (e.g., `003-user-auth`)
- Alternatively: if `init-options.json` contains `"feature_numbering": "timestamp"`, use `YYYYMMDD-HHMMSS-<slug>` instead

---

## Composed-Template Resolution Contract

When a command script runs (e.g. `~/.claude/skills/speckit/scripts/bash/resolve-template.sh spec-template --json`), it emits a JSON object containing `TEMPLATE_CONTENT` — the fully composed template after applying all layers.

Layer order (first match / highest priority wins per section):

1. **Override** — `<project>/.specify/templates/<name>.md` (project-specific override)
2. **Presets** — each preset listed in `<project>/.specify/presets/.registry`, sorted by priority descending
3. **Extensions** — each installed extension's template contribution, in registration order
4. **Core** — `~/.claude/skills/speckit/templates/<name>.md` (built-in fallback)

The script handles all merging. The agent receives only `TEMPLATE_CONTENT` (the composed result) and must not attempt to re-merge layers manually. If the script fails, the command must stop and report the error — never fall back to just the core template silently.
