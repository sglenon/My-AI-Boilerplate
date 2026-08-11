# V2 Orchestration Package

This directory contains the installable orchestration system for AI Excellence
Playbook v2. The package follows the boundaries in
[ADR 001](../docs/adr/001-v2-package-contract.md).

---

## Package Layout

```
orchestration/
├── README.md              # Package overview
├── INSTALL.md             # Authoritative AI-guided installation procedure
└── core/                  # Complete deployable orchestration package
```

The `core/` directory preserves the project-relative layout expected by Claude
Code. Its `CLAUDE.md`, `.claude/`, and `sonarqube/` paths are source templates
for installation into a target project.

---

## Core Workflow

```
master plans
  → worker implements
  → sonar reports static-analysis evidence
  → master reviews
  → worker fixes and the review loop repeats
  → commit owns Git and GitHub operations
```

Core includes all four agents, routing policy, session and bootstrap hooks,
project-scoped usage tracking, and the local SonarQube stack.

---

## Prerequisites

- Linux, WSL2, or macOS with Bash
- Claude Code CLI with agent-team support
- Python 3.10+
- Node.js and npm
- `jq`
- Docker with Docker Compose

Native Windows shells are not supported.

---

## Installation Status

The package is installed by an AI assistant following
[INSTALL.md](INSTALL.md).

Invoke it with:

```
Read orchestration/INSTALL.md and install AI Excellence Playbook v2 into:
<absolute-target-project-path>
```

For manual installation, use
[WORKSPACE_TEMPLATE.md](core/WORKSPACE_TEMPLATE.md) as the complete file
checklist.

---

## Installation Policy

V2 is installed as a new orchestration package. It does not upgrade previous
slash-command workflows. Remove conflicting commands or hooks before installing
v2.

The installer preserves unrelated project configuration, reports conflicts
before writing, and never performs Git mutations.

---

## Validation

Installation validates:

- Required core files
- Settings JSON
- Hook and scanner shell syntax
- Python usage parser
- Docker Compose configuration
- Secret and generated-file ignore rules
- Core model and tool boundaries

The installation remains partial until required prerequisites and the local
`.claude/sonar.env` file are present.

---

## Next Steps

After installation:

1. Complete the installed `sonarqube/INSTALL.md`.
2. Restart Claude Code.
3. Run the routing smoke test in `WORKSPACE_TEMPLATE.md`.
4. Review [Coding Techniques](../docs/04-coding-techniques.md).
