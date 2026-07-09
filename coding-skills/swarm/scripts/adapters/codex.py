"""codex.py — Codex CLI adapter. Uses `codex exec` non-interactively."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .base import ExecutorAdapter

# sys.path adjust for lib imports when run standalone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.shell import run as shell_run
from lib.tasks import write_status, now_iso
from lib.worktrees import collect_diff

# Real verified model in this environment.
DEFAULT_MODEL = "gpt-5.5"

# Auth failure markers in codex output
AUTH_MARKERS = ["401", "unauthorized", "not logged in", "authentication", "auth failed", "login required"]


class CodexAdapter(ExecutorAdapter):
    """
    Adapter for the Codex CLI (`codex exec`).

    Real model: gpt-5.5.
    PLAN.md labels codex-5.4-mini/codex-5.4 are NOT real — kept as disabled
    config entries only (see config.json).
    """

    name = "codex"

    def __init__(self, model: str = DEFAULT_MODEL, write_allowed: bool = True, timeout_minutes: int = 45, sandbox_mode: str = ""):
        self.model = model
        self.write_allowed = write_allowed
        self.timeout_seconds = timeout_minutes * 60
        self.sandbox_mode = sandbox_mode

    def available(self) -> bool:
        return shutil.which("codex") is not None

    def version(self) -> str:
        result = shell_run(["codex", "--version"], timeout=10)
        if result.ok():
            return result.stdout.strip() or result.stderr.strip() or "codex (version unknown)"
        return "codex (not available)"

    def run_task(
        self,
        task_dir: Path,
        worktree_dir: Path,
        config: dict,
    ) -> int:
        prompt_path = task_dir / "prompt.md"
        stdout_log = task_dir / "stdout.log"
        stderr_log = task_dir / "stderr.log"
        diff_path = task_dir / "diff.patch"

        if not self.available():
            msg = "codex not found on PATH. Install codex CLI and retry."
            write_status(task_dir, status="blocked", finished_at=now_iso(), summary=msg)
            stderr_log.write_text(msg, encoding="utf-8")
            return 1

        if not prompt_path.exists():
            msg = "prompt.md not found in task_dir"
            write_status(task_dir, status="blocked", finished_at=now_iso(), summary=msg)
            stderr_log.write_text(msg, encoding="utf-8")
            return 1

        prompt_text = prompt_path.read_text(encoding="utf-8")

        write_status(task_dir, status="running", started_at=now_iso(), executor=self.name)

        sandbox_mode = config.get("sandbox_mode", self.sandbox_mode)

        cmd = ["codex", "exec", prompt_text]
        if self.model and sandbox_mode:
            cmd = ["codex", "exec", "-s", sandbox_mode, "-m", self.model, prompt_text]
        elif self.model:
            cmd = ["codex", "exec", "-m", self.model, prompt_text]
        elif sandbox_mode:
            cmd = ["codex", "exec", "-s", sandbox_mode, prompt_text]

        if sandbox_mode:
            with open(stderr_log, "a", encoding="utf-8") as f:
                f.write(f"SWARM: codex ran with sandbox_mode={sandbox_mode} (unsandboxed — bwrap namespaces blocked in this container; isolation via worktree+review+protected-path check)\n")

        result = shell_run(
            cmd,
            cwd=worktree_dir,
            timeout=self.timeout_seconds,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )

        # Detect auth failure
        combined = (result.stdout + result.stderr).lower()
        is_auth_failure = any(m in combined for m in AUTH_MARKERS)

        if is_auth_failure:
            msg = "codex auth failure — run `codex login` then retry this task"
            write_status(
                task_dir,
                status="blocked",
                finished_at=now_iso(),
                exit_code=result.returncode,
                summary=msg,
            )
            with open(stderr_log, "a", encoding="utf-8") as f:
                f.write(f"\n\nSWARM: {msg}\n")
            return result.returncode

        # Collect diff
        collect_diff(worktree_dir, diff_path)

        if result.ok():
            write_allowed = config.get("write_allowed", self.write_allowed)
            diff_empty = not diff_path.exists() or diff_path.stat().st_size == 0

            # For write-capable tasks, an empty diff after exit code 0 may indicate
            # that codex's internal bwrap sandbox blocked the write. The CLI itself
            # succeeds (exit 0) but no changes land on disk. Flag for human review.
            if write_allowed and diff_empty:
                status = "needs_review"
                summary = (
                    "codex exec exit_code=0 but diff.patch is empty on a write-capable task. "
                    "This may indicate codex's internal bwrap sandbox blocked file writes. "
                    "See troubleshooting.md: 'Codex Sandbox Write-Block'. "
                    "Check codex sandbox config or use the Codex plugin (CODEX_PLUGIN_SETUP.md)."
                )
            else:
                status = "done"
                summary = f"codex exec exit_code={result.returncode}"
        else:
            status = "failed"
            summary = f"codex exec exit_code={result.returncode}"

        write_status(
            task_dir,
            status=status,
            finished_at=now_iso(),
            exit_code=result.returncode,
            summary=summary,
        )

        return result.returncode
