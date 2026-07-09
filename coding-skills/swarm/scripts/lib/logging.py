"""logging.py — run directory layout creation and swarm.log management."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path


def create_run_dir(base: Path, run_id: str) -> Path:
    """
    Create full run directory layout under base/run_id/.
    Layout per PLAN.md §12:
      goal.md, plan.md, plan.json, router-decisions.md
      tasks/
      review/
      applied/
      swarm.log
    """
    run_dir = base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    for subdir in ("tasks", "review", "applied"):
        (run_dir / subdir).mkdir(exist_ok=True)

    # Initialize files if missing
    for fname, content in [
        ("goal.md", "# Goal\n\n"),
        ("plan.md", "# Plan\n\n"),
        ("plan.json", "{}"),
        ("router-decisions.md", "# Router Decisions\n\n"),
        ("swarm.log", ""),
    ]:
        fpath = run_dir / fname
        if not fpath.exists():
            fpath.write_text(content, encoding="utf-8")

    return run_dir


def log(run_dir: Path, message: str, level: str = "INFO") -> None:
    """Append a line to swarm.log."""
    log_path = run_dir / "swarm.log"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] [{level}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def write_goal(run_dir: Path, goal: str) -> None:
    (run_dir / "goal.md").write_text(f"# Goal\n\n{goal}\n", encoding="utf-8")


def write_plan(run_dir: Path, plan_text: str, plan_json: dict | None = None) -> None:
    import json
    (run_dir / "plan.md").write_text(f"# Plan\n\n{plan_text}\n", encoding="utf-8")
    if plan_json is not None:
        (run_dir / "plan.json").write_text(json.dumps(plan_json, indent=2), encoding="utf-8")


def write_router_decision(run_dir: Path, task_id: str, executor: str, reason: str) -> None:
    path = run_dir / "router-decisions.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n## {task_id} → {executor} ({ts})\n{reason}\n")
