"""tasks.py — task directory creation, status.json management, prompt rendering."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


STATUS_SCHEMA = {
    "run_id": "",
    "task_id": "",
    "executor": "",
    "status": "pending",
    "started_at": "",
    "finished_at": "",
    "worktree": "",
    "exit_code": None,
    "tests_passed": None,
    "summary": "",
    "revision": 1,
    "parent_task": "",
    "base_task": "",
    "verdict": "",
    "review_path": "",
}


def create_task_dir(run_dir: Path, task_id: str) -> Path:
    """Create tasks/<task_id>/ directory tree and return path."""
    task_dir = run_dir / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def write_status(task_dir: Path, **kwargs) -> Path:
    """Write or update status.json in task_dir. Returns path."""
    status_path = task_dir / "status.json"
    if status_path.exists():
        existing = json.loads(status_path.read_text(encoding="utf-8"))
    else:
        existing = dict(STATUS_SCHEMA)

    existing.update(kwargs)
    status_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return status_path


def read_status(task_dir: Path) -> dict[str, Any]:
    """Read status.json from task_dir."""
    status_path = task_dir / "status.json"
    if status_path.exists():
        return json.loads(status_path.read_text(encoding="utf-8"))
    return dict(STATUS_SCHEMA)


def parse_task_id(task_id: str) -> tuple[str, int]:
    """Parse a task_id into (base, revision) tuple.

    "T001"     -> ("T001", 1)
    "T001-r2"  -> ("T001", 2)
    "T010-r11" -> ("T010", 11)
    Malformed suffix (non-integer) -> returns (task_id, 1) without crashing.
    """
    m = re.match(r"^(.+)-r(\d+)$", task_id)
    if m:
        try:
            return m.group(1), int(m.group(2))
        except ValueError:
            pass
    return task_id, 1


def revision_task_id(base: str, rev: int) -> str:
    """Build a task_id string from base and revision number.

    ("T001", 1)  -> "T001"   (rev 1 = no suffix for consistency with parse)
    ("T001", 2)  -> "T001-r2"
    ("T010", 11) -> "T010-r11"
    """
    if rev <= 1:
        return base
    return f"{base}-r{rev}"


def latest_revision(tasks_dir: Path, base_task: str) -> tuple[Optional[Path], int]:
    """Scan tasks_dir for task dirs matching base_task, return (dir, rev) of highest revision.

    Uses integer sort (not lexical), so T001-r10 sorts after T001-r2.
    Returns (None, 0) if no matching dirs found.
    """
    if not tasks_dir.exists():
        return None, 0

    best_dir: Optional[Path] = None
    best_rev = 0

    for d in tasks_dir.iterdir():
        if not d.is_dir():
            continue
        try:
            found_base, rev = parse_task_id(d.name)
        except Exception:
            continue
        if found_base == base_task:
            if rev > best_rev:
                best_rev = rev
                best_dir = d

    return best_dir, best_rev


def render_prompt(
    template_path: Path,
    task_dir: Path,
    run_id: str,
    task_id: str,
    repo: str,
    base_branch: str,
    worktree: str,
    executor: str,
    goal: str,
    context: str,
    files_in_scope: list[str],
    files_out_of_scope: list[str],
    validation_command: str,
    prior_attempt: str = "",
    fix_instructions: str = "",
) -> Path:
    """Render handoff-template.md into task_dir/prompt.md."""
    template = template_path.read_text(encoding="utf-8")

    _none_str = "(none — first attempt)"
    replacements = {
        "{{run_id}}": run_id,
        "{{task_id}}": task_id,
        "{{repo}}": repo,
        "{{base_branch}}": base_branch,
        "{{worktree}}": worktree,
        "{{executor}}": executor,
        "{{goal}}": goal,
        "{{context}}": context,
        "{{files_in_scope}}": "\n".join(f"- {f}" for f in files_in_scope) if files_in_scope else "- (none specified)",
        "{{files_out_of_scope}}": "\n".join(f"- {f}" for f in files_out_of_scope) if files_out_of_scope else "- (none specified)",
        "{{validation_command}}": validation_command or "(manual — no test command detected)",
        "{{task_dir}}": str(task_dir),
        "{{prior_attempt}}": prior_attempt if prior_attempt else _none_str,
        "{{fix_instructions}}": fix_instructions if fix_instructions else _none_str,
    }

    rendered = template
    for k, v in replacements.items():
        rendered = rendered.replace(k, v)

    prompt_path = task_dir / "prompt.md"
    prompt_path.write_text(rendered, encoding="utf-8")
    return prompt_path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id(slug: str) -> str:
    """Create a run ID like 20260709T151600-add-subtract."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    safe_slug = re.sub(r"[^a-z0-9-]", "-", slug.lower().strip())[:40].strip("-")
    return f"{ts}-{safe_slug}"
