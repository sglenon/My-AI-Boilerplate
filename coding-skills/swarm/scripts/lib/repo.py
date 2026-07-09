"""repo.py — git repo detection, test command auto-detect, protected glob matching."""
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path
from typing import Optional


def detect_git_root(cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the git root for cwd, or None if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def detect_test_command(repo_root: Path) -> str:
    """Auto-detect the test command for a repo. Returns empty string if unknown."""
    # package.json → npm/pnpm test
    pkg_json = repo_root / "package.json"
    if pkg_json.exists():
        # Check for pnpm-lock.yaml
        if (repo_root / "pnpm-lock.yaml").exists():
            return "pnpm test"
        return "npm test"

    # pyproject.toml — check uv.lock for uv run pytest, else pytest
    if (repo_root / "pyproject.toml").exists():
        # Check tests/ dir exists
        tests_dir = repo_root / "tests"
        if (repo_root / "uv.lock").exists():
            if tests_dir.exists():
                return "uv run pytest"
            return ""  # no tests dir found; mark manual
        return "pytest" if tests_dir.exists() else ""

    # requirements.txt
    if (repo_root / "requirements.txt").exists():
        tests_dir = repo_root / "tests"
        return "pytest" if tests_dir.exists() else ""

    # Cargo.toml
    if (repo_root / "Cargo.toml").exists():
        return "cargo test"

    # go.mod
    if (repo_root / "go.mod").exists():
        return "go test ./..."

    return ""


def is_protected(path: str, protected_globs: list[str]) -> bool:
    """Return True if path matches any protected glob pattern.

    Handles two gap cases beyond plain fnmatch:
    a. Patterns starting with "**/" (e.g. "**/*secret*") — fnmatch requires a
       literal "/" to be present in the candidate, so top-level files like
       "secret.txt" are not matched.  We also test the pattern with the "**/"
       prefix stripped against the full path and the basename.
    b. Directory-prefix patterns ending in "/" with no wildcards (e.g.
       "migrations/") — fnmatch never matches file paths under that directory.
       We check via str.startswith instead.
    """
    basename = Path(path).name
    for pattern in protected_globs:
        # Direct fnmatch on full path and basename.
        if fnmatch.fnmatch(path, pattern):
            return True
        if fnmatch.fnmatch(basename, pattern):
            return True
        # (a) "**/" prefix: strip it and try on full path + basename.
        if pattern.startswith("**/"):
            stripped = pattern[3:]  # e.g. "*secret*" from "**/*secret*"
            if fnmatch.fnmatch(path, stripped):
                return True
            if fnmatch.fnmatch(basename, stripped):
                return True
        # (b) Directory-style pattern ending in "/" with no wildcard chars:
        #     treat as "any file whose path starts with this prefix".
        if pattern.endswith("/") and "*" not in pattern and "?" not in pattern:
            if path.startswith(pattern):
                return True
    return False


def get_repo_name(repo_root: Path) -> str:
    """Return the repo directory name."""
    return repo_root.name


def get_current_branch(repo_root: Path) -> str:
    """Return current branch name, or 'HEAD' if detached."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return "HEAD"
