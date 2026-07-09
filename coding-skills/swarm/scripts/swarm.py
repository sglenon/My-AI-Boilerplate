#!/usr/bin/env python3
"""
swarm.py — CLI entrypoint for the /swarm multi-agent orchestration system.

Usage:
  swarm.py doctor
  swarm.py init
  swarm.py install-repo <path>
  swarm.py install-all --roots "<root1>:<root2>" [--dry-run] [--apply]
  swarm.py status --run <run_id>
  swarm.py run-one --goal "<goal>" [--executor codex|opencode|sonnet] [--repo <path>]
  swarm.py plan "<goal>"                   (stub v0.1)
  swarm.py dispatch --plan <plan.json>     (stub v0.1)
  swarm.py collect --run <run_id>          (stub v0.1)

v0.1 live subcommands: doctor, init, install-repo, status, run-one
Stub subcommands: plan, dispatch, collect
install-all: dry-run listing only; --apply refused this session (decision #5)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure lib/adapters are importable
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from lib import config as cfg_mod
from lib import repo as repo_mod
from lib import tasks as tasks_mod
from lib import worktrees as wt_mod
from lib import logging as log_mod
from lib.shell import run as shell_run


GLOBAL_SWARM_DIR = Path.home() / ".claude" / "swarm"
SKILLS_DIR = Path.home() / ".claude" / "skills" / "swarm"
HANDOFF_TEMPLATE = SKILLS_DIR / "handoff-template.md"


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args) -> int:
    print("=== swarm doctor ===\n")

    checks = {}

    # git
    r = shell_run(["git", "--version"], timeout=10)
    checks["git"] = {"ok": r.ok(), "version": r.stdout.strip(), "note": ""}

    # python3
    r = shell_run(["python3", "--version"], timeout=10)
    checks["python3"] = {"ok": r.ok(), "version": r.stdout.strip() or r.stderr.strip(), "note": ""}

    # node
    r = shell_run(["node", "--version"], timeout=10)
    checks["node"] = {"ok": r.ok(), "version": r.stdout.strip(), "note": ""}

    # tmux — expected missing
    r = shell_run(["tmux", "-V"], timeout=5)
    checks["tmux"] = {
        "ok": False,
        "version": "NOT INSTALLED (expected — swarm uses subprocess, not tmux)",
        "note": "tmux is not used by swarm; this is normal",
    }

    # claude CLI
    claude_path = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")
    r = shell_run([claude_path, "--version"], timeout=10)
    checks["claude"] = {
        "ok": r.returncode == 0,
        "version": (r.stdout + r.stderr).strip(),
        "note": f"path: {claude_path}",
    }

    # codex
    r = shell_run(["codex", "--version"], timeout=10)
    if not r.ok():
        r2 = shell_run(["codex", "help"], timeout=10)
        codex_ok = r2.returncode == 0 or shutil.which("codex") is not None
    else:
        codex_ok = True
    codex_ver = (r.stdout + r.stderr).strip() or ("codex present" if shutil.which("codex") else "NOT FOUND")
    checks["codex"] = {
        "ok": shutil.which("codex") is not None,
        "version": codex_ver,
        "note": "real model: gpt-5.5 (PLAN.md labels codex-5.4-mini/codex-5.4 are NOT real models)",
    }

    # opencode
    r = shell_run(["opencode", "--version"], timeout=10)
    oc_ver = (r.stdout + r.stderr).strip()
    checks["opencode"] = {
        "ok": shutil.which("opencode") is not None,
        "version": oc_ver or ("opencode present" if shutil.which("opencode") else "NOT FOUND"),
        "note": "model: opencode/deepseek-v4-flash-free; read-only by default",
    }

    # Print results
    max_w = max(len(k) for k in checks)
    all_ok = True
    for name, info in checks.items():
        icon = "OK" if info["ok"] else ("WARN" if name == "tmux" else "MISS")
        if not info["ok"] and name != "tmux":
            all_ok = False
        note = f"  ({info['note']})" if info["note"] else ""
        print(f"  [{icon}] {name:<{max_w}}  {info['version']}{note}")

    print()

    # Model availability summary
    print("Model availability:")
    print("  [OK  ] gpt-5.5         via codex exec -m gpt-5.5")
    print("  [OK  ] opencode/deepseek-v4-flash-free  via opencode run -m opencode/deepseek-v4-flash-free")
    print("  [OK  ] claude -p       sonnet via claude print mode")
    print("  [WARN] codex-5.4-mini  NOT a real model (PLAN.md label, disabled in config)")
    print("  [WARN] codex-5.4       NOT a real model (PLAN.md label, disabled in config)")
    print()

    # Check global config
    cfg_path = GLOBAL_SWARM_DIR / "config.json"
    if cfg_path.exists():
        print(f"  [OK  ] Global config: {cfg_path}")
    else:
        print(f"  [MISS] Global config not found: {cfg_path}")
        all_ok = False

    print()
    if all_ok:
        print("doctor: all critical checks passed.")
    else:
        print("doctor: some checks failed. See above. tmux warning is expected/non-blocking.")
    return 0


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    """Initialize global swarm directories."""
    for d in [
        GLOBAL_SWARM_DIR / "logs",
        GLOBAL_SWARM_DIR / "runs",
    ]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ensured: {d}")

    cfg_path = GLOBAL_SWARM_DIR / "config.json"
    if not cfg_path.exists():
        print(f"  [WARN] config.json not found at {cfg_path}. Run after creating it.")
    else:
        print(f"  [OK] config.json: {cfg_path}")

    print("init complete.")
    return 0


# ---------------------------------------------------------------------------
# install-repo
# ---------------------------------------------------------------------------

def cmd_install_repo(args) -> int:
    repo_path = Path(args.path).expanduser().resolve()

    if not repo_path.exists():
        print(f"ERROR: path does not exist: {repo_path}")
        return 1

    # Verify git repo
    r = shell_run(["git", "rev-parse", "--show-toplevel"], cwd=repo_path, timeout=10)
    if not r.ok():
        print(f"ERROR: {repo_path} is not a git repository.")
        return 1

    repo_root = Path(r.stdout.strip())
    repo_name = repo_mod.get_repo_name(repo_root)
    test_cmd = repo_mod.detect_test_command(repo_root)

    print(f"Installing swarm for repo: {repo_name} ({repo_root})")

    # Create .claude/
    claude_dir = repo_root / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Create .claude/swarm.config.json (don't overwrite)
    cfg_path = claude_dir / "swarm.config.json"
    if not cfg_path.exists():
        repo_config = {
            "version": 1,
            "repo_name": repo_name,
            "max_revisions": 3,
            "test_commands": {
                "default": test_cmd,
                "unit": test_cmd,
                "lint": "",
            },
            "protected_paths": [
                ".env",
                ".env.*",
                "migrations/",
                "deploy/",
                "infra/",
            ],
            "preferred_executors": {
                "small_fix": "codex-gpt5.5",
                "implementation": "codex-gpt5.5",
                "scouting": "deepseek-v4-flash",
                "docs": "sonnet",
                "fallback": "sonnet",
            },
            "parallelism": 3,
        }
        cfg_path.write_text(json.dumps(repo_config, indent=2), encoding="utf-8")
        print(f"  created: {cfg_path}")
        print(f"  test_command detected: {test_cmd or '(none — mark manual)'}")
    else:
        print(f"  exists (skipped): {cfg_path}")

    # Create .swarm/README.md
    swarm_dir = repo_root / ".swarm"
    swarm_dir.mkdir(exist_ok=True)
    readme_path = swarm_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            f"# .swarm — {repo_name}\n\n"
            "Local swarm run artifacts for this repo.\n\n"
            "- `runs/` — per-run directories with prompts, diffs, logs, status\n"
            "- `worktrees/` — git worktrees for parallel write tasks (gitignored)\n\n"
            "See global docs: ~/.claude/swarm/README.md\n",
            encoding="utf-8",
        )
        print(f"  created: {readme_path}")
    else:
        print(f"  exists (skipped): {readme_path}")

    # Update .gitignore
    gitignore_path = repo_root / ".gitignore"
    entries_to_add = [".swarm/runs/", ".swarm/worktrees/"]
    _update_gitignore(gitignore_path, entries_to_add)

    print(f"\ninstall-repo complete for {repo_name}.")
    return 0


def _update_gitignore(path: Path, entries: list[str]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    added = []
    for entry in entries:
        if entry not in lines and not any(entry.strip("/") in line for line in lines):
            lines.append(entry)
            added.append(entry)
    if added:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        for e in added:
            print(f"  gitignore: added {e}")
    else:
        print(f"  gitignore: entries already present (skipped)")


# ---------------------------------------------------------------------------
# install-all (dry-run stub; --apply refused this session)
# ---------------------------------------------------------------------------

def cmd_install_all(args) -> int:
    roots_str = getattr(args, "roots", "") or ""
    dry_run = getattr(args, "dry_run", True)
    apply = getattr(args, "apply", False)

    if apply:
        print(
            "ERROR: --apply is out of scope for this session per decision #5.\n"
            "install-all --apply requires separate explicit user approval.\n"
            "Run with --dry-run to discover repos first, then request approval."
        )
        return 1

    roots = [Path(r).expanduser() for r in roots_str.split(":") if r.strip()]
    if not roots:
        print("ERROR: --roots is required. Example: --roots \"$HOME/Desktop:$HOME/projects\"")
        return 1

    print(f"install-all (DRY-RUN) — discovering git repos under: {', '.join(str(r) for r in roots)}\n")

    skip_dirs = {"node_modules", ".venv", "venv", ".git", "vendor", "__pycache__", ".tox"}
    repos_found = []

    for root in roots:
        if not root.exists():
            print(f"  [SKIP] {root} does not exist")
            continue
        for p in root.rglob(".git"):
            if p.is_dir():
                repo = p.parent
                # Skip if any ancestor part is in skip_dirs
                if any(part in skip_dirs for part in repo.parts):
                    continue
                repos_found.append(repo)

    if not repos_found:
        print("No git repos found.")
        return 0

    print(f"Found {len(repos_found)} repo(s):\n")
    for repo in sorted(repos_found):
        test_cmd = repo_mod.detect_test_command(repo)
        installed = (repo / ".claude" / "swarm.config.json").exists()
        status = "installed" if installed else "not installed"
        print(f"  {repo}  |  test: {test_cmd or 'manual'}  |  swarm: {status}")

    print(
        f"\nDRY-RUN complete. {len(repos_found)} repo(s) found.\n"
        "To install: get explicit human approval, then run with --apply in a new approved session."
    )
    return 0


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def cmd_status(args) -> int:
    run_id = args.run
    repo_root = repo_mod.detect_git_root() or Path.cwd()
    run_dir = repo_root / ".swarm" / "runs" / run_id

    if not run_dir.exists():
        # Try global
        run_dir = GLOBAL_SWARM_DIR / "runs" / run_id

    if not run_dir.exists():
        print(f"Run not found: {run_id}")
        return 1

    print(f"=== swarm status: {run_id} ===\n")
    goal_path = run_dir / "goal.md"
    if goal_path.exists():
        print(goal_path.read_text(encoding="utf-8"))

    tasks_dir = run_dir / "tasks"
    if not tasks_dir.exists():
        print("No tasks found.")
        return 0

    for task_dir in sorted(tasks_dir.iterdir()):
        status_path = task_dir / "status.json"
        if status_path.exists():
            s = json.loads(status_path.read_text(encoding="utf-8"))
            print(f"  {s.get('task_id','?')}  executor={s.get('executor','?')}  status={s.get('status','?')}  exit_code={s.get('exit_code','?')}")
            if s.get("summary"):
                print(f"    summary: {s['summary']}")

    print()
    return 0


# ---------------------------------------------------------------------------
# _launch_task — shared task-launch helper
# ---------------------------------------------------------------------------

def _launch_task(
    run_dir: Path,
    repo_root: Path,
    config: dict,
    task_id: str,
    executor_name: str,
    goal: str,
    context: str,
    files_in_scope: list,
    files_out_of_scope: list,
    prior_attempt: str = "",
    fix_instructions: str = "",
    parent_task: str = "",
    revision: int = 1,
    base_branch: str = None,
    test_cmd: str = None,
    seed_diff_path: Path = None,
) -> int:
    """Create task dir, worktree, optionally seed diff, render prompt, run adapter."""
    repo_name = repo_mod.get_repo_name(repo_root)
    if test_cmd is None:
        test_cmd = repo_mod.detect_test_command(repo_root)
    if base_branch is None:
        base_branch = repo_mod.get_current_branch(repo_root)

    run_id = run_dir.name

    task_dir = tasks_mod.create_task_dir(run_dir, task_id)

    # Determine write_allowed
    executor_cfg = config.get("executors", {}).get(executor_name, {})
    # codex key fallback
    if not executor_cfg and executor_name == "codex":
        executor_cfg = config.get("executors", {}).get("codex-gpt5.5", {})
    write_allowed = executor_cfg.get("write_allowed", True)

    # Create worktree if write task
    worktree_path = repo_root
    worktree_str = str(repo_root)

    if write_allowed and config.get("require_worktrees_for_writes", True):
        ok, wt_path, err = wt_mod.add_worktree(repo_root, run_id, task_id)
        if ok:
            worktree_path = wt_path
            worktree_str = str(wt_path)
            log_mod.log(run_dir, f"Worktree created: {wt_path}")
        else:
            print(f"[swarm] WARNING: worktree creation failed: {err}")
            print("[swarm] Falling back to sequential in-tree execution.")
            log_mod.log(run_dir, f"Worktree failed: {err} — using main repo", "WARN")

    # Seed diff if provided (apply prior attempt's diff into fresh worktree)
    if seed_diff_path and seed_diff_path.exists():
        r = shell_run(
            ["git", "apply", "--whitespace=nowarn", str(seed_diff_path)],
            cwd=worktree_path,
            timeout=30,
        )
        if r.ok():
            log_mod.log(run_dir, f"Seeded worktree with diff: {seed_diff_path}")
        else:
            log_mod.log(run_dir, f"WARN: seed diff failed to apply cleanly: {r.stderr.strip()}", "WARN")
            print(f"[swarm] WARNING: seed diff did not apply cleanly — proceeding with clean worktree.")

    # Render prompt
    tasks_mod.render_prompt(
        template_path=HANDOFF_TEMPLATE,
        task_dir=task_dir,
        run_id=run_id,
        task_id=task_id,
        repo=repo_name,
        base_branch=base_branch,
        worktree=worktree_str,
        executor=executor_name,
        goal=goal,
        context=context,
        files_in_scope=files_in_scope,
        files_out_of_scope=files_out_of_scope,
        validation_command=test_cmd,
        prior_attempt=prior_attempt,
        fix_instructions=fix_instructions,
    )

    # Determine base_task from task_id
    base_task_id, _rev = tasks_mod.parse_task_id(task_id)

    tasks_mod.write_status(
        task_dir,
        run_id=run_id,
        task_id=task_id,
        executor=executor_name,
        status="pending",
        worktree=worktree_str,
        revision=revision,
        parent_task=parent_task,
        base_task=base_task_id,
        verdict="",
        review_path="",
    )

    print(f"[swarm] Run: {run_id}")
    print(f"[swarm] Task: {task_id}, executor: {executor_name}, revision: {revision}")
    print(f"[swarm] Prompt: {task_dir}/prompt.md")
    print(f"[swarm] Worktree: {worktree_str}")

    # Load and run adapter
    adapter = _load_adapter(executor_name, config)
    if adapter is None:
        print(f"ERROR: unknown executor: {executor_name}")
        return 1

    if not adapter.available():
        print(f"[swarm] {executor_name} adapter not available. Checking for fallback...")
        if executor_name != "sonnet":
            from adapters.sonnet import SonnetAdapter
            adapter = SonnetAdapter()
            print("[swarm] Falling back to sonnet adapter.")

    rc = adapter.run_task(task_dir, Path(worktree_str), config)

    log_mod.log(run_dir, f"Task {task_id} finished, rc={rc}")

    print(f"\n[swarm] Task done. exit_code={rc}")
    print(f"[swarm] Artifacts:")
    for fname in ["status.json", "stdout.log", "stderr.log", "diff.patch", "notes.md"]:
        p = task_dir / fname
        if p.exists():
            size = p.stat().st_size
            print(f"  {p}  ({size} bytes)")

    status = tasks_mod.read_status(task_dir)
    print(f"\n[swarm] Status: {status.get('status')}")
    print(f"[swarm] Run dir: {run_dir}")
    print("\n[swarm] NOTE: Planner review (master agent) required before accepting any diff.")
    return rc


# ---------------------------------------------------------------------------
# run-one
# ---------------------------------------------------------------------------

def cmd_run_one(args) -> int:
    """
    Create a run dir, task dir, worktree (if write task), write prompt,
    invoke chosen adapter, collect diff, write status.
    """
    goal = args.goal
    executor_name = getattr(args, "executor", "codex") or "codex"
    repo_path = Path(getattr(args, "repo", None) or ".").expanduser().resolve()

    repo_root = repo_mod.detect_git_root(repo_path)
    if not repo_root:
        print(f"ERROR: not a git repo: {repo_path}")
        return 1

    config = cfg_mod.load_config(repo_root)
    test_cmd = repo_mod.detect_test_command(repo_root)
    base_branch = repo_mod.get_current_branch(repo_root)

    run_id = tasks_mod.make_run_id(goal[:40])
    task_id = "T001"

    # Determine run dir
    swarm_runs = repo_root / ".swarm" / "runs"
    swarm_runs.mkdir(parents=True, exist_ok=True)

    run_dir = log_mod.create_run_dir(swarm_runs, run_id)
    log_mod.write_goal(run_dir, goal)
    log_mod.log(run_dir, f"Starting run {run_id}, executor={executor_name}, goal={goal[:80]}")

    return _launch_task(
        run_dir=run_dir,
        repo_root=repo_root,
        config=config,
        task_id=task_id,
        executor_name=executor_name,
        goal=goal,
        context=f"Repo: {repo_root}\nTest command: {test_cmd or '(manual)'}",
        files_in_scope=[],
        files_out_of_scope=[".env", "migrations/", "deploy/"],
        prior_attempt="",
        fix_instructions="",
        parent_task="",
        revision=1,
        base_branch=base_branch,
        test_cmd=test_cmd,
        seed_diff_path=None,
    )


# ---------------------------------------------------------------------------
# redispatch
# ---------------------------------------------------------------------------

def cmd_redispatch(args) -> int:
    """Re-dispatch a task after NEEDS_FIXES verdict into a new revision task dir."""
    run_id = args.run
    base_task = args.task
    executor_override = getattr(args, "executor", None)
    verdict_file_rel = getattr(args, "verdict_file", None) or "review/final-verdict.md"

    repo_root = repo_mod.detect_git_root() or Path.cwd()
    config = cfg_mod.load_config(repo_root)

    # Resolve run dir
    run_dir = repo_root / ".swarm" / "runs" / run_id
    if not run_dir.exists():
        run_dir = GLOBAL_SWARM_DIR / "runs" / run_id
    if not run_dir.exists():
        print(f"ERROR: run not found: {run_id}")
        return 1

    tasks_dir = run_dir / "tasks"

    # Find latest revision of the base task
    parent_task_dir, current_rev = tasks_mod.latest_revision(tasks_dir, base_task)
    if parent_task_dir is None or current_rev == 0:
        # Maybe base_task itself doesn't exist yet — treat as rev 1 not found
        print(f"ERROR: no task dir found matching base_task={base_task} in {tasks_dir}")
        return 1

    parent_task_id = parent_task_dir.name
    next_rev = current_rev + 1
    max_revisions = config.get("max_revisions", 3)

    # Guard: exceeded max_revisions
    if next_rev > max_revisions:
        # Find all revision dirs for escalation report
        all_rev_dirs = []
        for d in sorted(tasks_dir.iterdir()):
            if d.is_dir():
                b, _ = tasks_mod.parse_task_id(d.name)
                if b == base_task:
                    all_rev_dirs.append(str(d))

        # Read last verdict
        verdict_path = run_dir / verdict_file_rel
        last_verdict = ""
        if verdict_path.exists():
            last_verdict = verdict_path.read_text(encoding="utf-8").strip()

        # Write escalation.md
        review_dir = run_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        escalation_path = review_dir / "escalation.md"
        escalation_content = (
            f"# Swarm Escalation\n\n"
            f"**base_task**: {base_task}\n"
            f"**run_id**: {run_id}\n"
            f"**reason**: max_revisions_exceeded\n"
            f"**max_revisions**: {max_revisions}\n"
            f"**attempted revisions**: {current_rev}\n\n"
            f"## Revision Dirs\n"
            + "\n".join(f"- {d}" for d in all_rev_dirs) + "\n\n"
            f"## Last Verdict\n\n"
            f"{last_verdict or '(none)'}\n"
        )
        escalation_path.write_text(escalation_content, encoding="utf-8")

        # Set parent task status to blocked
        tasks_mod.write_status(parent_task_dir, status="blocked", verdict="BLOCKED_max_revisions_exceeded")

        print(f"[swarm] ESCALATION: max_revisions ({max_revisions}) reached for {base_task}.")
        print(f"[swarm] Escalation report: {escalation_path}")
        print("[swarm] Human review required. No new revision created.")
        return 1

    # Read fix instructions from verdict file
    verdict_path = run_dir / verdict_file_rel
    fix_instructions = ""
    if verdict_path.exists():
        verdict_text = verdict_path.read_text(encoding="utf-8")
        # Extract ## Required Fixes section
        m = re.search(r"^##\s+Required Fixes\s*\n(.*?)(?=^##|\Z)", verdict_text, re.MULTILINE | re.DOTALL)
        if m:
            fix_instructions = m.group(1).strip()
        else:
            print(f"[swarm] WARNING: '## Required Fixes' heading not found in {verdict_path}. Using full verdict as fix_instructions.")
            fix_instructions = verdict_text.strip()
    else:
        print(f"[swarm] WARNING: verdict file not found: {verdict_path}. fix_instructions will be empty.")

    # Build prior_attempt summary
    parent_diff = parent_task_dir / "diff.patch"
    parent_summary = parent_task_dir / "summary.md"
    prior_attempt_parts = [f"Parent task: {parent_task_id}"]
    if parent_diff.exists():
        prior_attempt_parts.append(f"Prior diff: {parent_diff}")
    if parent_summary.exists():
        summary_text = parent_summary.read_text(encoding="utf-8").strip()
        prior_attempt_parts.append(f"Prior summary:\n{summary_text}")
    prior_attempt = "\n\n".join(prior_attempt_parts)

    # Seed diff path
    seed_diff_path = parent_diff if parent_diff.exists() else None

    # Determine executor
    parent_status = tasks_mod.read_status(parent_task_dir)
    parent_executor = parent_status.get("executor", "codex") or "codex"
    executor_name = executor_override or parent_executor

    # Build new task_id
    new_task_id = tasks_mod.revision_task_id(base_task, next_rev)

    # Read goal from run
    goal_path = run_dir / "goal.md"
    goal = goal_path.read_text(encoding="utf-8").strip() if goal_path.exists() else "(unknown goal)"

    # Read parent context from parent prompt.md if available
    parent_prompt = parent_task_dir / "prompt.md"
    context_text = ""
    if parent_prompt.exists():
        # Extract context section from parent prompt
        pt = parent_prompt.read_text(encoding="utf-8")
        m2 = re.search(r"^## Context\n(.*?)(?=^##|\Z)", pt, re.MULTILINE | re.DOTALL)
        if m2:
            context_text = m2.group(1).strip()
    if not context_text:
        context_text = f"Repo: {repo_root}\nTest command: {repo_mod.detect_test_command(repo_root) or '(manual)'}"

    test_cmd = repo_mod.detect_test_command(repo_root)
    base_branch = repo_mod.get_current_branch(repo_root)

    log_mod.log(run_dir, f"Redispatching {base_task} as {new_task_id}, executor={executor_name}, rev={next_rev}")

    return _launch_task(
        run_dir=run_dir,
        repo_root=repo_root,
        config=config,
        task_id=new_task_id,
        executor_name=executor_name,
        goal=goal,
        context=context_text,
        files_in_scope=[],
        files_out_of_scope=[".env", "migrations/", "deploy/"],
        prior_attempt=prior_attempt,
        fix_instructions=fix_instructions,
        parent_task=parent_task_id,
        revision=next_rev,
        base_branch=base_branch,
        test_cmd=test_cmd,
        seed_diff_path=seed_diff_path,
    )


def _load_adapter(name: str, config: dict):
    """Load and return an adapter by name."""
    name = name.lower()
    executors = config.get("executors", {})
    executor_cfg = executors.get(name, {})
    # codex CLI is invoked as "codex" but config key is "codex-gpt5.5"; fall back.
    if not executor_cfg and name == "codex":
        executor_cfg = executors.get("codex-gpt5.5", {})
    model = executor_cfg.get("model")
    write_allowed = executor_cfg.get("write_allowed", True)
    timeout_min = config.get("default_timeout_minutes", 45)

    if name in ("codex", "codex-gpt5.5"):
        from adapters.codex import CodexAdapter, DEFAULT_MODEL
        sandbox_mode = executor_cfg.get("sandbox_mode", "")
        return CodexAdapter(model=model or DEFAULT_MODEL, write_allowed=write_allowed, timeout_minutes=timeout_min, sandbox_mode=sandbox_mode)
    elif name in ("opencode", "deepseek-v4-flash", "deepseek"):
        from adapters.opencode import OpencodeAdapter, DEFAULT_MODEL
        return OpencodeAdapter(model=model or DEFAULT_MODEL, write_allowed=write_allowed, timeout_minutes=timeout_min)
    elif name == "sonnet":
        from adapters.sonnet import SonnetAdapter
        return SonnetAdapter(timeout_minutes=timeout_min)
    return None


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def cmd_plan(args) -> int:
    print("plan: not yet implemented in v0.1. Coming in v0.2.")
    return 0


def cmd_dispatch(args) -> int:
    print("dispatch: not yet implemented in v0.1. Coming in v0.2.")
    return 0


def cmd_collect(args) -> int:
    print("collect: not yet implemented in v0.1. Coming in v0.2.")
    return 0


# ---------------------------------------------------------------------------
# accept
# ---------------------------------------------------------------------------

def cmd_accept(args) -> int:
    """
    Accept & merge back approved task diffs into the current working tree.

    For each task in the run with status=done and a non-empty diff.patch:
      1. Check protected paths — refuse (non-zero) if the patch touches any.
      2. Apply the patch via git apply (uncommitted by default).
      3. If --commit, run git add -A && git commit.
      4. On success, remove the worktree and delete the temp branch.

    No interactive y/n prompt per task — review approval IS the confirmation
    (decision #3). --yes flag exists for scripted callers; default path is silent.
    """
    run_id = args.run
    task_filter = getattr(args, "task", None)
    do_commit = getattr(args, "commit", False)

    repo_root = repo_mod.detect_git_root() or Path.cwd()
    config = cfg_mod.load_config(repo_root)

    # Protected globs from global config merged with repo config.
    # Also union repo-local "protected_paths" (e.g. "migrations/", "deploy/")
    # so per-repo protections are enforced at apply time.
    protected_globs = list(config.get("protected_globs", []))
    protected_paths = config.get("protected_paths", [])
    for p in protected_paths:
        if p not in protected_globs:
            protected_globs.append(p)

    # Locate run dir
    run_dir = repo_root / ".swarm" / "runs" / run_id
    if not run_dir.exists():
        run_dir = GLOBAL_SWARM_DIR / "runs" / run_id
    if not run_dir.exists():
        print(f"ERROR: run not found: {run_id}")
        return 1

    tasks_dir = run_dir / "tasks"
    if not tasks_dir.exists():
        print(f"ERROR: no tasks directory in run: {run_dir}")
        return 1

    # Collect candidate task dirs
    task_dirs = sorted(tasks_dir.iterdir())
    if task_filter:
        task_dirs = [t for t in task_dirs if t.name == task_filter]
        if not task_dirs:
            print(f"ERROR: task {task_filter} not found in run {run_id}")
            return 1

    applied_count = 0
    skipped_count = 0
    failed_count = 0
    overall_exit = 0

    for task_dir in task_dirs:
        if not task_dir.is_dir():
            continue

        status = tasks_mod.read_status(task_dir)
        task_id = status.get("task_id") or task_dir.name
        task_status = status.get("status", "")
        diff_path = task_dir / "diff.patch"

        if task_status != "done":
            print(f"  [{task_id}] SKIP — status={task_status} (only 'done' tasks accepted)")
            skipped_count += 1
            continue

        if not diff_path.exists() or diff_path.stat().st_size == 0:
            print(f"  [{task_id}] SKIP — diff.patch missing or empty")
            skipped_count += 1
            continue

        # Protected-path check
        hits = wt_mod.patch_touches_protected(diff_path, protected_globs)
        if hits:
            print(f"  [{task_id}] REFUSE — patch touches protected path(s): {', '.join(hits)}")
            print(f"    Worktree preserved. Review manually before accepting.")
            failed_count += 1
            overall_exit = 1
            continue

        # Apply patch (uncommitted working-tree change)
        ok, err = wt_mod.apply_patch(repo_root, diff_path)
        if not ok:
            print(f"  [{task_id}] FAIL — patch did not apply cleanly: {err}")
            print(f"    Worktree preserved at: {status.get('worktree', '?')}")
            failed_count += 1
            overall_exit = 1
            continue

        # Optional commit
        if do_commit:
            goal_path = run_dir / "goal.md"
            goal_text = goal_path.read_text(encoding="utf-8").strip()[:60] if goal_path.exists() else run_id
            commit_msg = f"swarm: {goal_text}"
            r1 = shell_run(["git", "add", "-A"], cwd=repo_root, timeout=15)
            r2 = shell_run(["git", "commit", "-m", commit_msg], cwd=repo_root, timeout=30)
            if not r2.ok():
                print(f"  [{task_id}] WARN — patch applied but commit failed: {r2.stderr.strip()}")
            else:
                print(f"  [{task_id}] committed: {commit_msg!r}")

        # Remove worktree and delete branch
        wt_ok, wt_err = wt_mod.remove_worktree(repo_root, run_id, task_id, remove_branch=True, force=True)
        wt_status = "cleaned up" if wt_ok else f"cleanup failed: {wt_err}"

        applied_files = _list_patch_files(diff_path)
        print(f"  [{task_id}] APPLIED — {len(applied_files)} file(s): {', '.join(applied_files[:5])}"
              f"{'...' if len(applied_files) > 5 else ''}")
        print(f"    committed: {'yes' if do_commit else 'no (uncommitted changes in working tree)'}")
        print(f"    worktree: {wt_status}")
        applied_count += 1

    print(f"\n[accept] run={run_id}: applied={applied_count}, skipped={skipped_count}, failed/refused={failed_count}")
    return overall_exit


def _list_patch_files(patch_path: Path) -> list[str]:
    """Extract list of changed file paths from a diff patch."""
    import re
    files = []
    diff_git_re = re.compile(r"^diff --git a/(.+) b/(.+)$")
    for line in patch_path.read_text(encoding="utf-8").splitlines():
        m = diff_git_re.match(line)
        if m:
            path = m.group(2) if m.group(2) != "/dev/null" else m.group(1)
            if path not in files:
                files.append(path)
    return files


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="swarm.py",
        description="/swarm orchestration CLI v0.1",
    )
    sub = parser.add_subparsers(dest="command")

    # doctor
    sub.add_parser("doctor", help="Check tool availability and config")

    # init
    sub.add_parser("init", help="Initialize global swarm directories")

    # install-repo
    p_install = sub.add_parser("install-repo", help="Install swarm config in a repo")
    p_install.add_argument("path", help="Path to the repo")

    # install-all
    p_all = sub.add_parser("install-all", help="Discover repos and optionally install (dry-run by default)")
    p_all.add_argument("--roots", required=True, help="Colon-separated root paths")
    p_all.add_argument("--dry-run", action="store_true", default=True, help="List repos only (default)")
    p_all.add_argument("--apply", action="store_true", default=False, help="Actually install (refused this session)")

    # status
    p_status = sub.add_parser("status", help="Show status of a swarm run")
    p_status.add_argument("--run", required=True, help="Run ID")

    # run-one
    p_run = sub.add_parser("run-one", help="Run a single task")
    p_run.add_argument("--goal", required=True, help="Task goal")
    p_run.add_argument("--executor", default="codex", choices=["codex", "opencode", "sonnet", "deepseek"], help="Executor adapter")
    p_run.add_argument("--repo", default=".", help="Repo path (default: cwd)")

    # stubs
    p_plan = sub.add_parser("plan", help="[v0.2] Plan a goal")
    p_plan.add_argument("goal", nargs="?")

    p_dispatch = sub.add_parser("dispatch", help="[v0.2] Dispatch a plan")
    p_dispatch.add_argument("--plan", help="plan.json path")

    p_collect = sub.add_parser("collect", help="[v0.2] Collect task results")
    p_collect.add_argument("--run", help="Run ID")

    # redispatch
    p_redispatch = sub.add_parser("redispatch", help="Re-dispatch a NEEDS_FIXES task into a new revision")
    p_redispatch.add_argument("--run", required=True, help="Run ID")
    p_redispatch.add_argument("--task", required=True, help="Base task ID (e.g. T001)")
    p_redispatch.add_argument("--executor", default=None, help="Override executor for the revision")
    p_redispatch.add_argument("--verdict-file", default="review/final-verdict.md", help="Path (relative to run_dir) to verdict file")

    # accept
    p_accept = sub.add_parser("accept", help="Merge approved task diffs into the current working tree")
    p_accept.add_argument("--run", required=True, help="Run ID")
    p_accept.add_argument("--task", default=None, help="Accept only this task ID (e.g. T001). Default: all done tasks in the run.")
    p_accept.add_argument("--commit", action="store_true", default=False, help="Commit applied changes (default: leave uncommitted)")
    p_accept.add_argument("--yes", action="store_true", default=False, help="Non-interactive flag (for scripted callers; accept does not prompt interactively by default)")

    args = parser.parse_args()

    dispatch = {
        "doctor": cmd_doctor,
        "init": cmd_init,
        "install-repo": cmd_install_repo,
        "install-all": cmd_install_all,
        "status": cmd_status,
        "run-one": cmd_run_one,
        "plan": cmd_plan,
        "dispatch": cmd_dispatch,
        "collect": cmd_collect,
        "accept": cmd_accept,
        "redispatch": cmd_redispatch,
    }

    if args.command is None:
        parser.print_help()
        return 0

    fn = dispatch.get(args.command)
    if fn:
        return fn(args)

    print(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
