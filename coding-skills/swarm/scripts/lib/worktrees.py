"""worktrees.py — git worktree management for swarm."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from .shell import run
from .repo import is_protected


def worktree_path(repo_root: Path, run_id: str, task_id: str) -> Path:
    return repo_root / ".swarm" / "worktrees" / run_id / task_id


def branch_name(run_id: str, task_id: str) -> str:
    return f"swarm/{run_id}/{task_id}"


def add_worktree(
    repo_root: Path,
    run_id: str,
    task_id: str,
) -> tuple[bool, Path, str]:
    """
    Create a git worktree for a task.
    Returns (success, worktree_path, error_message).
    Branch: swarm/<run_id>/<task_id>
    """
    wt_path = worktree_path(repo_root, run_id, task_id)
    branch = branch_name(run_id, task_id)

    wt_path.parent.mkdir(parents=True, exist_ok=True)

    result = run(
        ["git", "worktree", "add", str(wt_path), "-b", branch],
        cwd=repo_root,
        timeout=30,
    )

    if result.ok():
        return True, wt_path, ""
    return False, wt_path, result.stderr.strip()


def list_worktrees(repo_root: Path) -> list[dict]:
    """List all worktrees for a repo. Returns list of dicts with path/branch info."""
    result = run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        timeout=15,
    )
    if not result.ok():
        return []

    worktrees = []
    current: dict = {}
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[9:].strip()}
        elif line.startswith("branch "):
            current["branch"] = line[7:].strip()
        elif line.startswith("HEAD "):
            current["head"] = line[5:].strip()
    if current:
        worktrees.append(current)
    return worktrees


def remove_worktree(
    repo_root: Path,
    run_id: str,
    task_id: str,
    remove_branch: bool = True,
    force: bool = False,
) -> tuple[bool, str]:
    """
    Remove a worktree. Guarded: caller must ensure patch collected or approval given.
    Returns (success, error_message).
    """
    wt_path = worktree_path(repo_root, run_id, task_id)
    branch = branch_name(run_id, task_id)

    cmd = ["git", "worktree", "remove", str(wt_path)]
    if force:
        cmd.append("--force")

    result = run(cmd, cwd=repo_root, timeout=30)
    if not result.ok():
        return False, result.stderr.strip()

    if remove_branch:
        run(["git", "branch", "-D", branch], cwd=repo_root, timeout=15)

    return True, ""


def collect_diff(worktree_path: Path, output_path: Path) -> tuple[bool, str]:
    """
    Stage all changes in the worktree (git add -A), then produce a binary-capable
    cached diff that captures new, modified, and deleted files.  Writes the result
    to output_path (diff.patch).  Leaves the index staged (disposable worktree).
    Returns (success, error_message).

    Old plain `git diff` missed untracked/new files — this is the fix.
    """
    # Stage everything so new/untracked files appear in the diff
    add_result = run(
        ["git", "add", "-A"],
        cwd=worktree_path,
        timeout=30,
    )
    if add_result.returncode != 0:
        return False, f"git add -A failed: {add_result.stderr.strip()}"

    # --binary so binary files don't produce a broken patch
    result = run(
        ["git", "diff", "--cached", "--binary"],
        cwd=worktree_path,
        timeout=30,
    )
    output_path.write_text(result.stdout, encoding="utf-8")

    if result.returncode not in (0, 1):
        return False, result.stderr.strip()
    return True, ""


def apply_patch(repo_root: Path, patch_path: Path) -> tuple[bool, str]:
    """
    Apply patch_path into repo_root's working tree as uncommitted changes.
    Uses `git apply` without --index so changes land as working-tree modifications,
    not staged/committed.
    Returns (ok, error_message).
    """
    if not patch_path.exists() or patch_path.stat().st_size == 0:
        return False, f"patch file missing or empty: {patch_path}"

    result = run(
        ["git", "apply", "--whitespace=nowarn", str(patch_path)],
        cwd=repo_root,
        timeout=60,
    )
    if result.ok():
        return True, ""
    return False, result.stderr.strip() or result.stdout.strip()


def patch_touches_protected(patch_path: Path, protected_globs: list[str]) -> list[str]:
    """
    Parse the diff --git headers in patch_path to find all touched file paths,
    then return those that match any of protected_globs.

    Parses lines like: diff --git a/<path> b/<path>
    Returns a list of matching protected paths (empty if none).
    """
    if not patch_path.exists() or patch_path.stat().st_size == 0:
        return []

    touched: list[str] = []
    diff_git_re = re.compile(r"^diff --git a/(.+) b/(.+)$")

    for line in patch_path.read_text(encoding="utf-8").splitlines():
        m = diff_git_re.match(line)
        if m:
            path_a = m.group(1)
            path_b = m.group(2)
            # Use the b/ path (destination) as canonical; fall back to a/ for deletes
            path = path_b if path_b and path_b != "/dev/null" else path_a
            if path not in touched:
                touched.append(path)

    hits = [p for p in touched if is_protected(p, protected_globs)]
    return hits
