"""test_redispatch_guard.py — redispatch guard tests."""
import json
import pytest
import types
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers to build a minimal fake run dir
# ---------------------------------------------------------------------------

def _make_fake_run(tmp_path: Path, base_task: str = "T001", revision: int = 1, with_diff: bool = True, with_verdict: bool = True):
    """Create a minimal fake run directory structure.

    Uses tmp_path/.swarm/runs/... to match what cmd_redispatch expects when
    detect_git_root is patched to return tmp_path.
    """
    run_dir = tmp_path / ".swarm" / "runs" / "20260709T120000-test-goal"
    tasks_dir = run_dir / "tasks"

    task_id = base_task if revision == 1 else f"{base_task}-r{revision}"
    task_dir = tasks_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    # Write status.json
    status = {
        "run_id": run_dir.name,
        "task_id": task_id,
        "executor": "codex",
        "status": "needs_review",
        "started_at": "",
        "finished_at": "",
        "worktree": str(task_dir),
        "exit_code": 1,
        "tests_passed": None,
        "summary": "",
        "revision": revision,
        "parent_task": "",
        "base_task": base_task,
        "verdict": "",
        "review_path": "",
    }
    (task_dir / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

    if with_diff:
        # Write a trivial (empty) diff.patch so seed_diff_path exists
        (task_dir / "diff.patch").write_text("", encoding="utf-8")

    if with_verdict:
        # Write a verdict file with ## Required Fixes section
        review_dir = run_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        verdict_text = (
            "# Verdict\n\nNEEDS_FIXES\n\n"
            "## Required Fixes\n\n"
            "- Add null check on line 42\n"
            "- Handle empty input case\n"
        )
        (review_dir / "final-verdict.md").write_text(verdict_text, encoding="utf-8")

    # Write goal.md
    (run_dir / "goal.md").write_text("fix the bug", encoding="utf-8")

    return run_dir, task_dir


# ---------------------------------------------------------------------------
# No-op adapter stub
# ---------------------------------------------------------------------------

class NoOpAdapter:
    def available(self):
        return True

    def run_task(self, task_dir, worktree_path, config):
        return 0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_swarm_for_test(monkeypatch, tmp_path):
    """Patch swarm.py internals so tests don't need real git repos or CLIs."""
    import swarm

    # Patch _load_adapter to return no-op
    monkeypatch.setattr(swarm, "_load_adapter", lambda name, config: NoOpAdapter())

    # Patch repo detection to return tmp_path as repo root
    monkeypatch.setattr(swarm.repo_mod, "detect_git_root", lambda path=None: tmp_path)
    monkeypatch.setattr(swarm.repo_mod, "get_repo_name", lambda root: "test-repo")
    monkeypatch.setattr(swarm.repo_mod, "detect_test_command", lambda root: "pytest")
    monkeypatch.setattr(swarm.repo_mod, "get_current_branch", lambda root: "main")

    # Patch worktree creation to return the task dir itself (no real git ops)
    def fake_add_worktree(repo_root, run_id, task_id):
        wt_path = repo_root / ".swarm" / "worktrees" / run_id / task_id
        wt_path.mkdir(parents=True, exist_ok=True)
        return True, wt_path, ""

    monkeypatch.setattr(swarm.wt_mod, "add_worktree", fake_add_worktree)

    # Patch log_mod to be silent
    monkeypatch.setattr(swarm.log_mod, "log", lambda run_dir, msg, level="INFO": None)
    monkeypatch.setattr(swarm.log_mod, "create_run_dir", lambda runs_dir, run_id: runs_dir / run_id)
    monkeypatch.setattr(swarm.log_mod, "write_goal", lambda run_dir, goal: None)

    # Point GLOBAL_SWARM_DIR to tmp_path to avoid touching real fs
    monkeypatch.setattr(swarm, "GLOBAL_SWARM_DIR", tmp_path / "global_swarm")


# ---------------------------------------------------------------------------
# Tests: max_revisions guard
# ---------------------------------------------------------------------------

def test_redispatch_past_max_revisions_writes_escalation(tmp_path):
    """When next_rev > max_revisions, must write escalation.md, not create new dir."""
    import swarm

    # Create 3 revisions (at max_revisions=3 limit)
    run_dir, _ = _make_fake_run(tmp_path, "T001", revision=1)
    for rev in range(2, 4):  # T001-r2, T001-r3
        _make_fake_run(tmp_path, "T001", revision=rev)

    config = {"max_revisions": 3, "require_worktrees_for_writes": False, "executors": {}}
    monkeypatch_swarm_config(swarm, config, tmp_path)

    args = types.SimpleNamespace(
        run=run_dir.name,
        task="T001",
        executor=None,
        verdict_file="review/final-verdict.md",
    )

    # Override GLOBAL_SWARM_DIR and repo detection to point at our tmp structure
    original_detect = swarm.repo_mod.detect_git_root
    swarm.repo_mod.detect_git_root = lambda path=None: tmp_path

    rc = swarm.cmd_redispatch(args)

    assert rc == 1, "Should return 1 when max_revisions exceeded"

    escalation_path = run_dir / "review" / "escalation.md"
    assert escalation_path.exists(), "escalation.md must be written"

    content = escalation_path.read_text(encoding="utf-8")
    assert "max_revisions_exceeded" in content
    assert "T001" in content

    # No new revision dir should have been created
    tasks_dir = run_dir / "tasks"
    task_dirs = [d.name for d in tasks_dir.iterdir() if d.is_dir()]
    assert "T001-r4" not in task_dirs, "No T001-r4 should be created"


def test_redispatch_past_max_revisions_sets_status_blocked(tmp_path):
    """On max_revisions exceeded, parent task's status.json should become 'blocked'."""
    import swarm

    run_dir, _ = _make_fake_run(tmp_path, "T001", revision=1)
    for rev in range(2, 4):
        _make_fake_run(tmp_path, "T001", revision=rev)

    config = {"max_revisions": 3, "require_worktrees_for_writes": False, "executors": {}}
    monkeypatch_swarm_config(swarm, config, tmp_path)

    args = types.SimpleNamespace(
        run=run_dir.name,
        task="T001",
        executor=None,
        verdict_file="review/final-verdict.md",
    )

    swarm.cmd_redispatch(args)

    # T001-r3 is the latest (parent) — check its status
    parent_task_dir = run_dir / "tasks" / "T001-r3"
    status = json.loads((parent_task_dir / "status.json").read_text())
    assert status["status"] == "blocked"


def test_redispatch_under_max_creates_new_dir(tmp_path):
    """Under max_revisions, redispatch should create T001-r2 with correct fields."""
    import swarm

    run_dir, _ = _make_fake_run(tmp_path, "T001", revision=1)

    config = {"max_revisions": 3, "require_worktrees_for_writes": False, "executors": {}}
    monkeypatch_swarm_config(swarm, config, tmp_path)

    args = types.SimpleNamespace(
        run=run_dir.name,
        task="T001",
        executor=None,
        verdict_file="review/final-verdict.md",
    )

    rc = swarm.cmd_redispatch(args)
    assert rc == 0, f"Should succeed (rc=0), got {rc}"

    new_task_dir = run_dir / "tasks" / "T001-r2"
    assert new_task_dir.exists(), "T001-r2 directory should be created"

    status_path = new_task_dir / "status.json"
    assert status_path.exists(), "status.json should be written in T001-r2"

    status = json.loads(status_path.read_text())
    assert status["revision"] == 2
    assert status["parent_task"] == "T001"
    assert status["base_task"] == "T001"


def test_redispatch_under_max_prompt_contains_fix_instructions(tmp_path):
    """Under max_revisions, prompt.md in new revision dir should contain fix instructions."""
    import swarm

    run_dir, _ = _make_fake_run(tmp_path, "T001", revision=1)

    config = {"max_revisions": 3, "require_worktrees_for_writes": False, "executors": {}}
    monkeypatch_swarm_config(swarm, config, tmp_path)

    args = types.SimpleNamespace(
        run=run_dir.name,
        task="T001",
        executor=None,
        verdict_file="review/final-verdict.md",
    )

    swarm.cmd_redispatch(args)

    new_task_dir = run_dir / "tasks" / "T001-r2"
    prompt_path = new_task_dir / "prompt.md"
    assert prompt_path.exists(), "prompt.md should exist in T001-r2"

    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "Add null check on line 42" in prompt_text or "Handle empty input case" in prompt_text, \
        "Fix instructions from verdict file should appear in prompt"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def monkeypatch_swarm_config(swarm_module, config: dict, tmp_path: Path):
    """Patch cfg_mod.load_config to return given config dict."""
    swarm_module.cfg_mod.load_config = lambda repo_root=None: config
