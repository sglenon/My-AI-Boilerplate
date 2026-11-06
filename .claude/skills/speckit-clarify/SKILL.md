---
name: speckit-clarify
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec. Reads the active feature directory via check-prerequisites.sh.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before clarification)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_clarify` key
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

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `speckit-plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `~/.claude/skills/speckit/scripts/bash/check-prerequisites.sh --json --paths-only` from repo root **once**. Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   - If JSON parsing fails, abort and instruct user to re-run `speckit-specify` or verify feature branch environment.

2. **IF EXISTS**: Load `.specify/memory/constitution.md` for project principles and governance constraints.

3. Load the current spec file. Perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing.

   Categories to scan:
   - Functional Scope & Behavior (core user goals, out-of-scope declarations, user roles)
   - Domain & Data Model (entities, identity rules, lifecycle/state transitions, scale assumptions)
   - Interaction & UX Flow (critical user journeys, error/empty/loading states, accessibility)
   - Non-Functional Quality Attributes (performance, scalability, reliability, observability, security, compliance)
   - Integration & External Dependencies (external services/APIs, data formats, protocol/versioning)
   - Edge Cases & Failure Handling (negative scenarios, rate limiting, conflict resolution)
   - Constraints & Tradeoffs (technical constraints, rejected alternatives)
   - Terminology & Consistency (canonical glossary, avoided synonyms)
   - Completion Signals (acceptance criteria testability, measurable DoD indicators)
   - Misc / Placeholders (TODO markers, ambiguous adjectives lacking quantification)

4. Generate (internally) a prioritized queue of candidate clarification questions (maximum 5). Apply these constraints:
   - Maximum of 5 total questions across the whole session.
   - Each question must be answerable with EITHER a short multiple-choice selection (2–5 options) OR a one-word / short-phrase answer.
   - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.
   - Favor clarifications that reduce downstream rework risk.

5. Sequential questioning loop (interactive):
   - Present EXACTLY ONE question at a time.
   - For multiple-choice: analyze all options, determine the most suitable, present your recommendation prominently with reasoning, then render options as a Markdown table.
   - After the user answers, validate and record in working memory, then move to the next queued question.
   - Stop asking further questions when: all critical ambiguities resolved, user signals completion, or you reach 5 asked questions.
   - Never reveal future queued questions in advance.

6. Integration after EACH accepted answer (incremental update approach):
   - Ensure a `## Clarifications` section exists (create it if missing).
   - Under it, create (if not present) a `### Session YYYY-MM-DD` subheading for today.
   - Append a bullet line: `- Q: <question> → A: <final answer>`.
   - Apply the clarification to the most appropriate section(s) in the spec.
   - If the clarification invalidates an earlier ambiguous statement, replace that statement.
   - Save the spec file AFTER each integration to minimize risk of context loss.

7. Validation (performed after EACH write plus final pass):
   - Clarifications session contains exactly one bullet per accepted answer (no duplicates).
   - Total asked (accepted) questions ≤ 5.
   - Updated sections contain no lingering vague placeholders the new answer was meant to resolve.
   - No contradictory earlier statement remains.
   - Markdown structure valid.

8. Write the updated spec back to `FEATURE_SPEC`.

9. **Re-validate Spec Quality Checklist** (if `FEATURE_DIR/checklists/requirements.md` exists): re-evaluate each checkbox item against the updated spec, update checked/unchecked state as appropriate, save the checklist file.

Behavior rules:
- If no meaningful ambiguities found, respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- If spec file missing, instruct user to run `speckit-specify` first.
- Never exceed 5 total asked questions.
- Respect user early termination signals ("stop", "done", "proceed").

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_clarify`, skip to the Completion Report.
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

Report completion (after questioning loop ends or early termination):
- Number of questions asked & answered.
- Path to updated spec.
- Sections touched (list names).
- Spec quality checklist status (if `FEATURE_DIR/checklists/requirements.md` was re-validated): show before/after pass counts and list items that changed state.
- Coverage summary table listing each taxonomy category with Status: Resolved / Deferred / Clear / Outstanding.
- Suggested next command.

## Done When

- [ ] Spec ambiguities identified and clarifications integrated into spec file
- [ ] Spec quality checklist re-validated against updated spec (if `FEATURE_DIR/checklists/requirements.md` exists)
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported to user with questions answered, sections touched, checklist status, and coverage summary

Next: run `speckit-plan`
