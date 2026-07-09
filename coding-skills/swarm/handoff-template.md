# Swarm Worker Task

## Run
- run_id: {{run_id}}
- task_id: {{task_id}}
- repo: {{repo}}
- base_branch: {{base_branch}}
- worktree: {{worktree}}
- executor: {{executor}}

## Goal
{{goal}}

## Context
{{context}}

## Prior Attempt (rejected)
{{prior_attempt}}

## Required Fixes (from reviewer)
{{fix_instructions}}

## Files In Scope
{{files_in_scope}}

## Files Out of Scope
{{files_out_of_scope}}

## Constraints
- Do not commit.
- Do not push.
- Do not deploy.
- Do not modify secrets.
- Do not edit files outside scope unless necessary; if necessary, explain why in notes.md.
- Keep changes minimal.
- Prefer adding tests.
- Do not approve your own work.
- If this is a revision, you are a NEW worker. Address only the Required Fixes plus original Goal. Treat the Prior Attempt as reference, not as correct.

## Required Output
Write these files to the task directory ({{task_dir}}):
- status.json — final task status per schema
- summary.md — what was done, what was not done, why
- diff.patch — output of `git diff` from the worktree
- test.log — output of the validation command
- notes.md — anything unusual, scope expansions, blockers

## Validation Command
{{validation_command}}

## Stop Conditions
Stop and write status "blocked" when:
- Task is complete and tests pass (status: done)
- Blocked by missing dependency or auth requirement (status: blocked)
- Scope becomes larger than assigned (status: needs_review)
- A destructive action is required (status: blocked)
- Exit condition unclear — write notes and set status: needs_review
