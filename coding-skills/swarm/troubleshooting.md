# Swarm Troubleshooting — Known Limitations

## tmux Missing

tmux is NOT installed in this environment. All process management uses Python's `subprocess.Popen` and `subprocess.run`. Workers run sequentially or in parallel via threading — not tmux windows/panes. This is documented by design and does not degrade core functionality.

## Model Name Mismatches

PLAN.md originally referenced `codex-5.4-mini` and `codex-5.4`. These are **not real model identifiers** in the installed codex CLI. The verified real default model is `gpt-5.5`.

- `codex-5.4-mini` and `codex-5.4` entries appear in `config.json` as `"enabled": false` with a note explaining they are PLAN.md aliases pointing at gpt-5.5 and are unavailable.
- Do NOT hardcode these names in adapters or pass them to the codex CLI.
- The active codex executor uses `gpt-5.5`.

## Auth Failure Handling

### Codex
If codex returns a non-zero exit code with auth-related output (401, "unauthorized", "not logged in"), the adapter will:
1. Set `status: blocked` in `status.json`
2. Write the auth error to `stderr.log`
3. Print a clear message: "codex auth failure — run `codex login` then retry"
4. NOT fake success or silently skip the task

### opencode
If opencode returns auth failure for the deepseek provider:
1. Set `status: blocked`
2. Write error to `stderr.log`
3. Print: "opencode auth failure — run `opencode providers` to check credentials"

### claude CLI (sonnet adapter)
`claude -p` requires Anthropic credentials (ANTHROPIC_API_KEY or keychain). If unavailable:
1. Adapter writes `status: blocked`
2. Provides manual fallback: writes `prompt.md` to task dir with instruction to run manually

## opencode --auto Required for Non-Interactive Use

opencode requires `--auto` to approve directory access permissions in non-interactive/unattended mode. Without it, opencode auto-rejects external directory access with "permission requested: external_directory; auto-rejecting". The adapter includes `--auto` for all non-interactive invocations. This is verified in smoke testing.

## opencode Read-Only Enforcement (Scout Agent)

opencode/deepseek is configured `write_allowed: false` by default. This is intentional — deepseek is used for read-only scouting only. The adapter enforces read-only via a two-layer mechanism:

**Primary enforcement — opencode.json scout agent (empirically verified to work):**
Before invoking opencode for a scout task, the adapter writes an `opencode.json` to the worktree working directory defining a "scout" agent with all write, execute, and spawn tools disabled:

```json
{
  "agent": {
    "scout": {
      "tools": {
        "edit": false,
        "write": false,
        "bash": false,
        "patch": false,
        "task": false,
        "skill": false,
        "websearch": false
      }
    }
  }
}
```

opencode is then invoked with `--agent scout` so this constrained agent is used. With this config, available tools are reduced to glob/grep/read/todowrite — bash and write become "unavailable" to the model, preventing writes even when actively attempted.

**Why `task: false` is load-bearing:**
A project-level `permission: {edit: deny, bash: deny}` config is NOT sufficient. Empirically verified: the model can spawn a subagent via the `task` tool that inherits default allow-all permissions and writes files anyway (exit 0). Disabling `task` in the tools config stops this subagent-spawn bypass. This is the critical difference between the broken and working enforcement.

**Why `skill: false` and `websearch: false`:**
These close residual holes — global skills or websearch could potentially write files or exfiltrate data. A scout task has no legitimate need for either.

**Secondary enforcement (defense-in-depth):**
A prompt-text constraint `[CONSTRAINT: This is a READ-ONLY scouting task. Do not write or modify any files.]` is appended to the prompt. This is a soft layer only — the model can ignore text constraints. The opencode.json tools-deny config is the actual enforcement mechanism.

**What does NOT work (do not revert to these):**
- Prompt-text constraint alone: model can ignore it.
- `permission: {edit: deny, bash: deny}` in opencode.json: bypassable via `task` tool subagent spawn that inherits allow-all defaults. Empirically verified — model wrote a file and exited 0 despite the permission deny config.

## Sonnet Recursion Caveat

`claude -p` invokes a new claude session. This is a non-interactive print-mode invocation, not a recursive self-call in the current session. It works but:
- Each invocation starts fresh with no session context
- Tool access may be limited vs interactive mode
- If `-p` invocation fails, the adapter falls back to writing `prompt.md` with a manual fallback message

Verified flag: `-p`/`--print` (confirmed via `claude --help`).

## install-all Scope

`swarm.py install-all` is a **dry-run-only stub in v0.1**. It will discover git repos under given roots and list them. It will NOT write any files to other repos without `--apply`. Even with `--apply`, the current session does not run it against other repos — this requires separate explicit approval. See `~/.claude/swarm/README.md`.

## Worktree Isolation

If `git worktree add` fails (e.g., repo does not support worktrees, disk space, or the branch already exists), the adapter degrades to sequential in-tree execution and logs a warning. Parallel write tasks are NOT run without worktrees.

## Codex Sandbox Write-Block

**Root cause:** bwrap (bubblewrap) user-namespace creation is blocked at the OS level in this container. This is not a codex config issue — `clone(CLONE_NEWUSER)` is rejected by the kernel. Codex's `read-only` and `workspace-write` sandbox modes both rely on bwrap namespaces and are non-functional here. There is no swarm-side fix for a kernel-level restriction.

**Resolution:** The codex adapter runs with `-s danger-full-access` (set via `sandbox_mode: "danger-full-access"` in `config.json` on the `codex-gpt5.5` executor entry). This flag sets the sandbox *policy* only — it is narrower than `--dangerously-bypass-approvals-and-sandbox` (which was used in earlier manual testing) and does not bypass codex's approval prompts. The adapter logs a note to `stderr.log` for every run using this mode so it is visible in artifacts and not silent.

**Isolation without codex's own sandbox:** Since codex-internal confinement is absent, there is no runtime guard intercepting codex's writes mid-task (unlike the sonnet adapter which is covered by the PreToolUse hook). Swarm supplies three-layer isolation instead:
1. **Worktree isolation** — each write task runs in a disposable `git worktree` branch, never in the main working tree.
2. **Mandatory review gate** — every diff is reviewed by the master (planner) agent before `accept` is invoked. Worker output is never self-approved.
3. **Protected-path check at apply-time** — `swarm.py accept` calls `patch_touches_protected()` before applying any patch; if a protected glob matches, the task is refused and the worktree is preserved for manual inspection.

**Old behavior (before this fix):** The adapter would emit `needs_review` when a write-capable task exited 0 with an empty `diff.patch`, attributing it to a possible sandbox write-block. With `danger-full-access`, writes succeed and this false-positive path is no longer triggered for normal tasks. If `diff.patch` is still empty after a write task, it means codex genuinely made no changes — check `stdout.log` / `stderr.log`.

**Read-only / scout tasks** (`write_allowed: false`) produce an empty diff by design; the adapter does not flag those as `needs_review`.

## Empty Diffs on New-File-Only Tasks (collect_diff fix)

**Root cause (historical):** The old `collect_diff` used plain `git diff`, which only shows changes to tracked files. If a task only *created* new files (untracked), `git diff` produced an empty patch even though codex had written real output. This caused:
- False-positive `needs_review` status (empty diff heuristic misfire in the adapter)
- Manual hand-collection of files from the worktree to produce a usable patch (as observed in the first test session)
- Incorrect "no changes detected" verdicts from the planner reviewer

**Fix:** `collect_diff` now runs `git add -A` inside the worktree first (staging everything), then `git diff --cached --binary` to capture new, modified, and deleted files in a single binary-safe patch. The index is left staged — this is fine because the worktree is disposable. The resulting `diff.patch` correctly includes all changes regardless of whether files were pre-existing or newly created.

**Implication for `accept`:** `apply_patch` uses `git apply` without `--index`, so patches land as uncommitted working-tree modifications. `--commit` is available as opt-in. Protected-path check runs before apply.

## Known Sharp Edges

### sonnet adapter: --dangerously-skip-permissions on recursive claude -p

The sonnet adapter passes `--dangerously-skip-permissions` to the recursive `claude -p` invocation. This is required for non-interactive operation (recursive self-invocation cannot respond to interactive permission prompts), but it bypasses Claude Code's normal interactive permission gates. The **only remaining guardrail** on this path is the PreToolUse hook in `~/.claude/settings.json`, which now fails closed (exit code 2) when it detects dangerous patterns. If that hook is ever reverted to `|| true` (fail-open), this path becomes unguarded. Never remove the PreToolUse hook or revert it to fail-open while the sonnet adapter is in use.

## opencode --format json

opencode run supports `--format json` for structured output. The adapter uses this for reliable parsing. If JSON parsing fails, raw stdout is captured and logged.
