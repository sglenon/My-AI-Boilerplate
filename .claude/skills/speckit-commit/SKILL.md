---
name: speckit-commit
description: Stage and commit changes with a conventional commit message and an optional ticket tag. Human-gated — shows a full preview and requires explicit confirmation before running git commit. Never pushes, force-pushes, or amends.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may supply a commit type, description, ticket number, or any combination. If supplied, use those values and skip the corresponding resolution steps below.

---

## Overview

Build a conventional commit message, show a full preview to the user, and commit only after explicit confirmation. Never run `git push`, `git push --force`, `git commit --amend`, or `git commit --no-verify`.

---

## Step 1 — Inspect the working tree

Run both commands and record the output:

```bash
git status
git diff --stat
```

If there are no changes (working tree and index are clean), report "Nothing to commit — working tree is clean." and stop.

---

## Step 2 — Resolve ticket number

Try each source in order. Stop at the first hit.

### Source 1 — Zoho current-ticket file

Check whether `.specify/extensions/zoho/current-ticket.json` exists in the project root. If it exists, read its `ticket` field (or the first string-valued top-level key that looks like a ticket ID, e.g. `PROJ-123`). If found and non-empty, use that value as the ticket number and skip sources 2–4.

### Source 2 — Git branch name

Run:

```bash
git branch --show-current
```

Scan the branch name for a token matching the pattern `[A-Z][A-Z0-9]+-[0-9]+` (e.g. `PROJ-123`, `CRM-45`). If found, use it as the ticket number and skip sources 3–4.

### Source 3 — Active feature spec.md frontmatter

Locate the active feature directory using the same convention as the other speckit-* skills:

1. Check `SPECIFY_FEATURE_DIRECTORY` environment variable (absolute or relative to repo root).
2. Otherwise read `.specify/feature.json` and extract the `feature_directory` key (try `jq`, then `python3`, then `grep`/`sed` as fallback parsers — same order as `common.sh`).
3. If neither source yields a path, skip to Source 4.

Once the feature directory is resolved, read the YAML frontmatter of `<feature_dir>/spec.md` and look for a `ticket:` field. If found and non-empty, use that value and skip Source 4.

### Source 4 — Ask the user

None of the above yielded a ticket. Ask once:

```
No ticket found — proceed without one, or type a ticket number?
(Press Enter or type "none" to skip; type a ticket ID like PROJ-123 to use it.)
```

Wait for the user's reply. If they provide a ticket ID, use it. If they press Enter or type "none"/"skip", proceed without a ticket.

---

## Step 3 — Determine commit type and description

If the user supplied a type and description in their input, use them (validate the type against the allowed list below).

Otherwise, inspect the diff to infer the most appropriate type. Show the inferred type and description to the user as part of the confirmation step (Step 5) — they may correct them there.

Allowed types (conventional commits):
`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`, `revert`

If the user supplies a type that is not on this list, do not proceed silently. Ask them to pick from the list or accept an inferred type you propose. Never invent a type outside this list.

---

## Step 4 — Build the commit message

If a ticket number was resolved:

```
[TICKET-NO] type: short description
```

Example: `[PROJ-123] feat: add auth flow`

If no ticket number:

```
type: short description
```

Example: `feat: add auth flow`

The description must be a single line, imperative mood, no trailing period, max ~72 characters total (including the ticket tag).

---

## Step 5 — Show preview and ask for confirmation

Print the following block exactly, then wait for the user to respond:

```
Commit preview
──────────────
Message : [TICKET-NO] type: short description
                       (or "type: short description" if no ticket)

Files to be staged:
  <list each file that will be staged, one per line>

Type "yes" or "y" to commit, or anything else to cancel.
```

Do not run any git command until the user explicitly types `yes` or `y` (case-insensitive). Any other reply — including silence, "ok", "sure", or just pressing Enter — is a cancellation. On cancellation, report "Commit cancelled." and stop.

---

## Step 6 — Stage and commit

Only after explicit confirmation:

1. Stage each file individually by name. Do not use `git add -A` or `git add .`. Stage only files that are relevant to the change (the same files shown in the preview). If in doubt about a file, ask the user before staging it.

   ```bash
   git add path/to/file1 path/to/file2 ...
   ```

2. Commit using a heredoc to avoid shell-quoting issues with the message:

   ```bash
   git commit -m "$(cat <<'EOF'
   [TICKET-NO] type: short description
   EOF
   )"
   ```

3. Capture the resulting commit hash from `git log -1 --format="%h %s"`.

---

## Step 7 — Report

Print:

```
Committed: <hash> — <message>
```

Then stop. Do not push.

---

## Safety Rules

- Never run `git push` or any variant.
- Never run `git push --force`.
- Never run `git commit --amend`.
- Never run `git commit --no-verify`.
- Never stage files with `git add -A` or `git add .`.
- Never commit without the user typing an explicit affirmative (`yes` or `y`).
- Never invent a commit type outside the allowed list.
- Never resolve or read secrets or credentials files; `.specify/extensions/zoho/current-ticket.json` is read only for its ticket ID field.
