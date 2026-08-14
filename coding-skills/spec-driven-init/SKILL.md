---
name: spec-driven-init
description: Initialize or repair the self-contained Spec-Driven project runtime used by the Spec-Driven skill suite. Use when a repository lacks .specify scripts or templates, when another spec-driven-* skill needs its runtime, or when the user asks to set up spec-driven development without installing the Specify CLI or GitHub Spec Kit.
---

# Initialize Spec-Driven

Install the bundled project runtime into the target repository. This skill is self-contained and must not install or invoke the external `specify` CLI.

## Workflow

1. Resolve the repository root and this skill's directory.
2. Run:

   ```bash
   python3 <skill-directory>/scripts/init_project.py --project-root <repository-root>
   ```

3. Parse the JSON result and verify `ready` is `true`.
4. Report which files were created. Existing files are preserved.

Use `--check` for a read-only readiness check. If existing runtime files need replacement, inspect them and obtain explicit approval before overwriting them; the initializer intentionally copies only missing files.

## Runtime contract

The initializer provides:

- `.specify/scripts/python/` for deterministic feature and artifact setup
- `.specify/templates/` for specifications, plans, tasks, checklists, and constitutions
- `.specify/memory/constitution.md` for project governance
- `.specify/init-options.json` and `.specify/integration.json` for portable defaults

The runtime is based on GitHub Spec Kit v0.16.3 under the bundled MIT license, but it runs directly from the repository and has no Spec Kit installation dependency.
