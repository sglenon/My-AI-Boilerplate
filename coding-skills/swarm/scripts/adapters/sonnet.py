"""
sonnet.py — Claude CLI adapter using `claude -p` (non-interactive print mode).

Verified: claude --help confirms `-p`/`--print` for non-interactive output.
Falls back to writing prompt.md + manual instructions if invocation fails.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .base import ExecutorAdapter

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.shell import run as shell_run
from lib.tasks import write_status, now_iso
from lib.worktrees import collect_diff

# Verified via `claude --help`: -p / --print flag for non-interactive output
PRINT_FLAG = "-p"

AUTH_MARKERS = ["authentication", "unauthorized", "api key", "please login", "not authenticated"]


class SonnetAdapter(ExecutorAdapter):
    """
    Adapter for the claude CLI using `claude -p` non-interactive print mode.

    Per decision #4: attempt the invocation; if it fails or is unreliable,
    fall back to writing prompt.md + clear manual-fallback message.
    Never crashes or lies about success.
    """

    name = "sonnet"

    def __init__(self, timeout_minutes: int = 45):
        self.timeout_seconds = timeout_minutes * 60
        self._claude_path = shutil.which("claude") or "/home/lars-lenon/.local/bin/claude"

    def available(self) -> bool:
        return bool(shutil.which("claude") or Path("/home/lars-lenon/.local/bin/claude").exists())

    def version(self) -> str:
        result = shell_run([self._claude_path, "--version"], timeout=10)
        if result.returncode == 0:
            return result.stdout.strip() or result.stderr.strip() or "claude (version unknown)"
        return "claude (not available)"

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
            return self._manual_fallback(
                task_dir, stdout_log, stderr_log,
                reason="claude CLI not found on PATH"
            )

        if not prompt_path.exists():
            return self._manual_fallback(
                task_dir, stdout_log, stderr_log,
                reason="prompt.md not found in task_dir"
            )

        prompt_text = prompt_path.read_text(encoding="utf-8")

        write_status(task_dir, status="running", started_at=now_iso(), executor=self.name)

        # Attempt non-interactive invocation: claude -p "<prompt>"
        cmd = [
            self._claude_path,
            PRINT_FLAG,
            prompt_text,
            # SHARP EDGE: --dangerously-skip-permissions is required here because
            # recursive non-interactive claude -p invocations cannot respond to
            # interactive permission prompts. This bypasses Claude Code's normal
            # interactive permission gates on this recursive self-invocation path.
            # The ONLY remaining guardrail is the PreToolUse hook in
            # ~/.claude/settings.json, which fails closed (exit code 2) on
            # dangerous patterns. Never revert that hook to fail-open (|| true)
            # while this adapter is in use — doing so leaves this path unguarded.
            "--dangerously-skip-permissions",
        ]

        result = shell_run(
            cmd,
            cwd=worktree_dir,
            timeout=self.timeout_seconds,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )

        combined = (result.stdout + result.stderr).lower()

        # Detect auth failure
        if any(m in combined for m in AUTH_MARKERS) and result.returncode != 0:
            msg = (
                "claude CLI auth failure. Ensure ANTHROPIC_API_KEY is set or `claude` is authenticated.\n"
                f"Prompt saved to: {prompt_path}\n"
                "Run manually: claude -p \"$(cat prompt.md)\""
            )
            write_status(
                task_dir,
                status="blocked",
                finished_at=now_iso(),
                exit_code=result.returncode,
                summary="claude auth failure — manual fallback required",
            )
            with open(stderr_log, "a", encoding="utf-8") as f:
                f.write(f"\n\nSWARM: {msg}\n")
            return result.returncode

        # Detect if -p flag caused an interactive session start (non-zero rc with no useful output)
        if result.returncode != 0 and not result.stdout.strip():
            return self._manual_fallback(
                task_dir, stdout_log, stderr_log,
                reason=f"claude -p invocation failed (rc={result.returncode}), falling back to manual. stderr: {result.stderr[:200]}"
            )

        # Collect diff after successful run
        collect_diff(worktree_dir, diff_path)

        status = "done" if result.ok() else "failed"
        write_status(
            task_dir,
            status=status,
            finished_at=now_iso(),
            exit_code=result.returncode,
            summary=f"claude -p exit_code={result.returncode}",
        )

        return result.returncode

    def _manual_fallback(
        self,
        task_dir: Path,
        stdout_log: Path,
        stderr_log: Path,
        reason: str = "",
    ) -> int:
        """Write fallback message. Task must be completed manually."""
        prompt_path = task_dir / "prompt.md"
        fallback_msg = f"""SWARM MANUAL FALLBACK — sonnet adapter

Reason: {reason}

The claude CLI could not run this task non-interactively.
To complete this task manually:

1. Open Claude Code (interactive session).
2. Navigate to the worktree or repo directory.
3. Read the task prompt: {prompt_path}
4. Complete the task per the prompt instructions.
5. Run: git diff > {task_dir}/diff.patch
6. Update: {task_dir}/status.json  (set status to "done" or "failed")

Prompt file: {prompt_path}
"""
        stdout_log.write_text(fallback_msg, encoding="utf-8")
        stderr_log.write_text(reason, encoding="utf-8")

        write_status(
            task_dir,
            status="blocked",
            finished_at=now_iso(),
            exit_code=1,
            summary=f"sonnet manual fallback required: {reason[:200]}",
        )
        print(f"[swarm] MANUAL FALLBACK needed for sonnet task in {task_dir}")
        print(f"[swarm] Reason: {reason}")
        print(f"[swarm] See: {stdout_log}")
        return 1
