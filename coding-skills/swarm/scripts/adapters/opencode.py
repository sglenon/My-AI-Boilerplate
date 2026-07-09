"""opencode.py — opencode adapter. DeepSeek v4 Flash, read-only by default."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .base import ExecutorAdapter

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.shell import run as shell_run
from lib.tasks import write_status, now_iso

# Verified real model identifier for this environment
DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"

AUTH_MARKERS = ["401", "unauthorized", "not logged in", "authentication failed", "invalid api key", "auth failed"]

# Scout agent config written to worktree opencode.json for read-only enforcement.
# tools:task=false is load-bearing — it prevents the model from spawning subagents
# that inherit default allow-all permissions and can write despite the parent config.
# tools:skill=false and tools:websearch=false close residual exfiltration/write holes.
# Empirically verified: plain permission:{edit:deny,bash:deny} is bypassable via the
# task tool subagent spawn. This tools-deny config with task:false actually works.
SCOUT_AGENT_CONFIG = {
    "agent": {
        "scout": {
            "tools": {
                "edit": False,
                "write": False,
                "bash": False,
                "patch": False,
                "task": False,
                "skill": False,
                "websearch": False,
            }
        }
    }
}


def _write_scout_opencode_json(worktree_dir: Path) -> Path | None:
    """
    Write opencode.json with the scout agent config to worktree_dir.

    Returns the path written, or None if the directory doesn't exist.
    The scout agent disables all write/exec/spawn tools so the model physically
    cannot write files or bypass via subagent delegation.
    """
    if not worktree_dir.exists():
        return None
    config_path = worktree_dir / "opencode.json"
    config_path.write_text(json.dumps(SCOUT_AGENT_CONFIG, indent=2), encoding="utf-8")
    return config_path


class OpencodeAdapter(ExecutorAdapter):
    """
    Adapter for opencode CLI with DeepSeek v4 Flash.

    Invocation: opencode run -m opencode/deepseek-v4-flash-free "prompt" --format json
    Read-only by default (write_allowed: false in config).

    Read-only enforcement (write_allowed=False):
      1. Writes opencode.json scout agent config to worktree_dir with all write/exec/spawn
         tools disabled. This is the primary enforcement mechanism — empirically verified to
         prevent writes even when the model actively tries. The task tool is explicitly
         disabled (load-bearing) to prevent subagent-spawn bypass.
      2. Invokes opencode with --agent scout to select the constrained agent.
      3. Also appends a prompt-text constraint as defense-in-depth (secondary layer).
    """

    name = "opencode"

    def __init__(self, model: str = DEFAULT_MODEL, write_allowed: bool = False, timeout_minutes: int = 30):
        self.model = model
        self.write_allowed = write_allowed
        self.timeout_seconds = timeout_minutes * 60

    def available(self) -> bool:
        return shutil.which("opencode") is not None

    def version(self) -> str:
        result = shell_run(["opencode", "--version"], timeout=10)
        if result.returncode == 0:
            return result.stdout.strip() or result.stderr.strip() or "opencode (version unknown)"
        # opencode --version may print to stdout or stderr
        ver = (result.stdout + result.stderr).strip()
        return ver if ver else "opencode (not available)"

    def run_task(
        self,
        task_dir: Path,
        worktree_dir: Path,
        config: dict,
    ) -> int:
        prompt_path = task_dir / "prompt.md"
        stdout_log = task_dir / "stdout.log"
        stderr_log = task_dir / "stderr.log"

        if not self.available():
            msg = "opencode not found on PATH."
            write_status(task_dir, status="blocked", finished_at=now_iso(), summary=msg)
            stderr_log.write_text(msg, encoding="utf-8")
            return 1

        if not prompt_path.exists():
            msg = "prompt.md not found in task_dir"
            write_status(task_dir, status="blocked", finished_at=now_iso(), summary=msg)
            stderr_log.write_text(msg, encoding="utf-8")
            return 1

        prompt_text = prompt_path.read_text(encoding="utf-8")

        write_mode = config.get("write_allowed", self.write_allowed)

        if not write_mode:
            # Primary enforcement: write opencode.json scout agent with all write/exec/spawn
            # tools disabled. The model physically cannot write files with this config.
            # task:false is load-bearing — prevents subagent spawn bypass.
            _write_scout_opencode_json(worktree_dir)
            # Secondary enforcement (defense-in-depth): prompt-text constraint.
            prompt_text = prompt_text + "\n\n[CONSTRAINT: This is a READ-ONLY scouting task. Do not write or modify any files.]"

        write_status(task_dir, status="running", started_at=now_iso(), executor=self.name)

        cmd = [
            "opencode", "run",
            "-m", self.model,
            prompt_text,
            "--format", "json",
            "--auto",  # required for non-interactive use; auto-approves safe permissions
        ]

        if not write_mode:
            # Invoke with the scout agent defined in the opencode.json we wrote above.
            cmd += ["--agent", "scout"]

        result = shell_run(
            cmd,
            cwd=worktree_dir,
            timeout=self.timeout_seconds,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )

        combined = (result.stdout + result.stderr).lower()
        is_auth_failure = any(m in combined for m in AUTH_MARKERS)

        if is_auth_failure:
            msg = "opencode auth failure — run `opencode providers` to check credentials for deepseek"
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

        # Try to parse JSON output for structured result
        scout_summary = ""
        if result.stdout.strip():
            try:
                events = [json.loads(line) for line in result.stdout.strip().splitlines() if line.strip()]
                # Extract text from assistant messages
                texts = []
                for ev in events:
                    if isinstance(ev, dict):
                        t = ev.get("type", "")
                        if t == "text" or t == "message":
                            texts.append(str(ev.get("content", ev.get("text", ""))))
                scout_summary = "\n".join(texts)[:2000]
            except Exception:
                scout_summary = result.stdout[:2000]

        # Write scout summary to notes.md
        notes_path = task_dir / "notes.md"
        notes_path.write_text(f"# Scout Output\n\n{scout_summary}\n", encoding="utf-8")

        status = "done" if result.ok() else "failed"
        write_status(
            task_dir,
            status=status,
            finished_at=now_iso(),
            exit_code=result.returncode,
            summary=f"opencode exit_code={result.returncode}, read_only={not write_mode}",
        )

        return result.returncode
