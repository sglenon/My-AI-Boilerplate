---
name: staging-release
description: Cut a staging release branch off staging, cherry-pick a batch of tickets from dev, verify it, and open the PR. Use when the user gives a list of ticket codes marked Ready for Staging, or asks to cherry-pick, promote, or deploy tickets from dev to staging.
---

Promote a batch of tickets from `dev` to `staging` through a release branch.

**Never merge `dev` into `staging` and never push to `staging` directly.** `staging` is usually a cherry-pick line, not a descendant of `dev`. Fixing conflicts happens in the release branch so `staging` stays deployable.

## Step 0 — Preflight

```bash
git fetch origin
git status --short                                   # dirty tree?
git merge-base --is-ancestor origin/staging origin/dev && echo FF-POSSIBLE || echo DIVERGED
git rev-list --count origin/dev..origin/staging      # commits staging has that dev does not
```

Stash any dirty tree before you start. Tell the user the stash name so they can recover it.

```bash
git stash push -u -m "wip-before-staging-cherrypick"
```

## Step 1 — Map tickets to commits

The user gives ticket codes, not hashes. Resolve them:

```bash
git log --oneline --no-merges origin/staging..origin/dev | cat
```

Build a ticket → commit table. Watch for two traps:

- **One ticket, several commits.** A ticket often lands as 2–3 follow-up fixes. All of them must come.
- **One commit, several tickets.** Subjects like `[C-AO-I1457/I1459/I1460]` cover tickets that have no standalone commit. A plain `grep 'C-AO-I1459'` misses these.

## Step 2 — Drop what is already on staging

```bash
git cherry -v origin/staging origin/dev | grep '^-'
```

Lines marked `-` are already on `staging` as patch-equivalent commits. **Do not pick them.** Confirm with a content check before you tell the user a ticket is done:

```bash
git diff --stat origin/staging origin/dev -- <files touched by that commit>
```

## Step 3 — Find the dependency chain

**This is the step that decides whether the release works.** A clean cherry-pick is not proof the code runs.

For each ticket commit, ask what it builds on:

```bash
git show --stat <commit>                             # what files does it touch?
git ls-tree --name-only origin/staging <dir>/        # do those files exist on staging?
```

Red flags that mean the ticket cannot ship alone:

| Red flag | What to check |
|---|---|
| Adds a versioned file (`*.vX.Y.*`) | Does staging have the version it is based on? |
| Edits a manifest or config pointer | Does the target it points to exist on staging? |
| Imports a module | Does that module exist on staging? |
| Edits a file staging does not have | Find the commit that created it |

Trace the missing base back to its commit, then **pick the whole contiguous range** rather than a hand-picked list:

```bash
git log --oneline --reverse --no-merges <base>^..<tip> | cat
```

Name every extra ticket the range drags in. The user decides whether the extras may ship — they are the ones talking to the PM.

## Step 4 — Dry-run in a throwaway worktree

Never test on the real branch.

```bash
WT=/tmp/cp-dryrun
git worktree add --detach "$WT" origin/staging
git -C "$WT" cherry-pick $(git rev-list --reverse --no-merges <base>^..<tip>)
# ...inspect...
git worktree remove --force "$WT"
```

Use `git rev-list --no-merges`, not a plain `A..B` range. `git cherry-pick` aborts on a merge commit with `is a merge but no -m option was given`.

## Step 5 — Apply for real

```bash
git switch -c chore/staging-release-YYYY-MM-DD origin/staging
git cherry-pick $(git rev-list --reverse --no-merges <base>^..<tip>)
```

Cherry-pick stops on every commit already present, with `The previous cherry-pick is now empty`. That is expected, not an error. Git 2.45+ has `--empty=drop`; on older git, drain the sequencer:

```bash
GD=$(git rev-parse --git-dir)
for i in $(seq 1 40); do
  [ -f "$GD/CHERRY_PICK_HEAD" ] || { echo "done"; break; }
  if git diff --name-only --diff-filter=U | grep -q .; then
    echo "CONFLICT at $(git log -1 --format='%h %s' CHERRY_PICK_HEAD)"
    git diff --name-only --diff-filter=U
    break                       # stop and resolve by hand
  fi
  echo "skipped empty: $(git log -1 --format='%h %s' CHERRY_PICK_HEAD)"
  git cherry-pick --skip
done
```

Resolve real conflicts here, in the release branch.

Drop dev-only artifacts that ride along (log files, scratch docs, local dumps):

```bash
git rm -q dev.log && git commit -m "chore(staging): drop dev-only log file"
```

## Step 6 — Verify

**a. What did you leave out?** This is the check that proves nothing on the list is missing.

```bash
git diff --stat origin/dev
```

Every file listed must belong to a commit you excluded **on purpose**. Anything else means a ticket is incomplete.

**b. Config pointers resolve.** For manifest-driven repos, print the pointer file and confirm every path it names exists in the branch.

**c. Tests — compare to the dev baseline, never to zero.**

```bash
python -m pytest tests/ -q
```

Then run the same failing files on `origin/dev` and `origin/staging` in worktrees:

```bash
git worktree add --detach /tmp/wt-dev origin/dev
git worktree add --detach /tmp/wt-stg origin/staging
ln -s "$PWD/venv" /tmp/wt-dev/venv; ln -s "$PWD/venv" /tmp/wt-stg/venv
```

Classify each failure. Do not label anything "environment noise" until you have read the actual error:

| Group | Meaning | Blocks release? |
|---|---|---|
| Fails on dev **and** staging | Pre-existing. Own ticket. | No |
| Fails on dev **only** | Shipped broken from dev. Report it. | User decides |
| Fails on your branch **only** | **You broke it.** Fix before PR. | Yes |

Clean up every worktree when done: `git worktree remove --force <path>`.

## Step 7 — PR

```bash
git push -u origin chore/staging-release-YYYY-MM-DD
gh pr create --base staging --title "chore(staging): release batch — N tickets from dev" --body-file <path>
gh pr view <n> --json mergeable,mergeStateStatus
```

The PR body must state:

1. **Ticket table** — code, area, source commits.
2. **Extra dependencies** — every ticket not on the user's list, and why it had to come.
3. **Result** — commits picked, conflicts, empties skipped.
4. **Deliberately excluded** — what stayed on dev and why.
5. **Tests** — the baseline comparison table from Step 6c, with root causes.
6. **Reviewer checklist** — the decisions the PM or lead must make.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `is a merge but no -m option was given` | Range contains a merge commit | `git rev-list --no-merges` |
| `The previous cherry-pick is now empty` | Already on staging | `git cherry-pick --skip` |
| Picks clean, feature dead in staging | Missing base version or module | Step 3 — pick the dependency chain |
| CI green, extraction returns nothing | Manifest points at a file that does not exist | Step 6b |
| "Tests fail, I broke it" | Judged against zero, not against dev | Step 6c |
| Ticket looks missing after release | It landed inside a multi-ticket commit subject | Step 1 |

## 9ai-transform-project-service specifics

Manifest-driven surfaces — any ticket touching these needs the full Step 3 check, whatever the ticket count:

- `app/utils/nine_ai_transformer/prompt_library/transform.manifest.json` — the live pointer
- `extraction/extraction.manifest.vX.Y.json` and `parsing/parsing.manifest.vX.Y.json`
- `extraction/business/{project}/extraction_logic/batches/{batch}/vendor_registry/*.vX.Y.tmpl`
- `app/utils/nine_ai_transformer/providers/` — parser and chat providers

Print all three pointers on both branches before you plan the range:

```bash
git show origin/staging:app/utils/nine_ai_transformer/prompt_library/transform.manifest.json
git show origin/dev:app/utils/nine_ai_transformer/prompt_library/transform.manifest.json
```

Tickets touching only `app/prompts/` are usually safe to pick one by one at any count.
