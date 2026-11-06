---
name: speckit-specify
description: Create or update the feature specification from a natural language feature description. Resolves the spec-template, creates specs/NNN-<slug>/spec.md, and writes .specify/feature.json. Lazy-scaffolds .specify/ if absent.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Lazy Scaffold

If `<project>/.specify/` does not exist, create it first:
1. `mkdir -p .specify/memory .specify/templates`
2. Copy the 5 core templates from `~/.claude/skills/speckit/templates/` into `.specify/templates/`
3. Then proceed with the specification workflow below.

## Pre-Execution Checks

**Check for extension hooks (before specification)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_specify` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `speckit-{command-name}`
    Description: {description}

    Prompt: {prompt}
    To execute: run the `speckit-{command-name}` skill
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `speckit-{command-name}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
    After emitting the block above you MUST actually invoke the `speckit-{command-name}` skill and wait for it to finish before continuing. Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

The text the user typed after the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the feature:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance

2. **Branch creation** (optional, via hook):
   If a `before_specify` hook ran successfully in the Pre-Execution Checks above, it will have created/switched to a git branch and output JSON containing `BRANCH_NAME` and `FEATURE_NUM`. Note these values for reference, but the branch name does **not** dictate the spec directory name.

3. **Create the spec feature directory**:

   Specs live under the default `specs/` directory unless the user explicitly provides `SPECIFY_FEATURE_DIRECTORY`.

   **Resolution order for `SPECIFY_FEATURE_DIRECTORY`**:
   1. If the user explicitly provided `SPECIFY_FEATURE_DIRECTORY`, use it as-is
   2. Otherwise, auto-generate it under `specs/`:
      - Check `.specify/init-options.json` for `feature_numbering` (preferred)
      - If `"timestamp"`: prefix is `YYYYMMDD-HHMMSS` (current timestamp)
      - If `"sequential"` or absent: prefix is `NNN` (next available 3-digit number after scanning existing directories in `specs/`)
      - Construct the directory name: `<prefix>-<short-name>` (e.g., `003-user-auth`)
      - Set `SPECIFY_FEATURE_DIRECTORY` to `specs/<directory-name>`

   **Create the directory and spec file**:
   - `mkdir -p SPECIFY_FEATURE_DIRECTORY`
   - Resolve the active `spec-template` via `~/.claude/skills/speckit/scripts/bash/resolve-template.sh spec-template --json` and parse `TEMPLATE_CONTENT`
   - Copy the resolved template content to `SPECIFY_FEATURE_DIRECTORY/spec.md` as the starting point
   - Set `SPEC_FILE` to `SPECIFY_FEATURE_DIRECTORY/spec.md`
   - Persist the resolved path to `.specify/feature.json`:
     ```json
     {
       "feature_directory": "<resolved feature dir>"
     }
     ```
     Write the actual resolved directory path value (e.g., `specs/003-user-auth`), not the literal string `SPECIFY_FEATURE_DIRECTORY`.

   **IMPORTANT**:
   - You must only create one feature per invocation
   - The spec directory name and the git branch name are independent
   - The spec directory and file are always created by this skill, never by the hook

4. Load the resolved active `spec-template` file to understand required sections.

5. **IF EXISTS**: Load `.specify/memory/constitution.md` for project principles and governance constraints.

6. Follow this execution flow:
    1. Parse user description from arguments. If empty: ERROR "No feature description provided"
    2. Extract key concepts from description: actors, actions, data, constraints
    3. For unclear aspects:
       - Make informed guesses based on context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if: the choice significantly impacts feature scope or user experience; multiple reasonable interpretations exist with different implications; no reasonable default exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: scope > security/privacy > user experience > technical details
    4. Fill User Scenarios & Testing section. If no clear user flow: ERROR "Cannot determine user scenarios"
    5. Generate Functional Requirements — each requirement must be testable; use reasonable defaults for unspecified details (document assumptions in Assumptions section)
    6. Define Success Criteria — create measurable, technology-agnostic outcomes; include both quantitative metrics and qualitative measures; each criterion must be verifiable without implementation details
    7. Identify Key Entities (if data involved)
    8. Return: SUCCESS (spec ready for planning)

7. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description while preserving section order and headings.

8. **Specification Quality Validation**: After writing the initial spec, validate it against quality criteria and create `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md`. Re-run validation until all items pass (max 3 iterations). Handle [NEEDS CLARIFICATION] markers (max 3) by presenting options to the user before resolving them.

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_specify`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_specify` key.
- Filter out hooks where `enabled` is explicitly `false`.
- For each remaining executable hook (no non-empty `condition`), output based on `optional` flag:
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `speckit-{command-name}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the `speckit-{command-name}` skill and wait for it to finish before continuing.
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `speckit-{command-name}`
    Description: {description}

    Prompt: {prompt}
    To execute: run the `speckit-{command-name}` skill
    ```

## Completion Report

Report completion to the user with:
- `SPECIFY_FEATURE_DIRECTORY` — the feature directory path
- `SPEC_FILE` — the spec file path
- Checklist results summary
- Readiness for the next phase (`speckit-clarify` or `speckit-plan`)

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure).
- Written for business stakeholders, not developers.

### Success Criteria Guidelines

Success criteria must be measurable (specific metrics), technology-agnostic (no frameworks/languages/databases), user-focused (outcomes from user/business perspective), and verifiable without implementation details.

**Good examples**: "Users can complete checkout in under 3 minutes", "System supports 10,000 concurrent users"
**Bad examples**: "API response time is under 200ms" (too technical), "React components render efficiently" (framework-specific)

## Done When

- [ ] Specification written to `SPEC_FILE` and validated against quality checklist
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported to user with feature directory, spec file path, and checklist results

Next: run `speckit-clarify` or `speckit-plan`
