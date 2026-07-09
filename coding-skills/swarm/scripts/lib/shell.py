"""shell.py — subprocess wrapper for swarm. No tmux."""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Optional


class RunResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def ok(self) -> bool:
        return self.returncode == 0

    def __repr__(self) -> str:
        return f"RunResult(rc={self.returncode}, stdout={self.stdout[:80]!r})"


def run(
    cmd: list[str] | str,
    cwd: Optional[Path] = None,
    timeout: Optional[int] = None,
    stdout_log: Optional[Path] = None,
    stderr_log: Optional[Path] = None,
    env: Optional[dict] = None,
    shell: bool = False,
) -> RunResult:
    """Run a command and capture output. Write logs if paths given. No tmux."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            shell=shell,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        rc = proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = f"TIMEOUT after {timeout}s\n" + ((e.stderr or b"").decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
        rc = -1
    except FileNotFoundError as e:
        stdout = ""
        stderr = f"Command not found: {e}"
        rc = 127

    if stdout_log:
        stdout_log.parent.mkdir(parents=True, exist_ok=True)
        stdout_log.write_text(stdout, encoding="utf-8")
    if stderr_log:
        stderr_log.parent.mkdir(parents=True, exist_ok=True)
        stderr_log.write_text(stderr, encoding="utf-8")

    return RunResult(rc, stdout, stderr)


def run_streaming(
    cmd: list[str] | str,
    cwd: Optional[Path] = None,
    timeout: Optional[int] = None,
    stdout_log: Optional[Path] = None,
    stderr_log: Optional[Path] = None,
    env: Optional[dict] = None,
) -> RunResult:
    """Run command, stream output to logs in real time, return final result."""
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    if stdout_log:
        stdout_log.parent.mkdir(parents=True, exist_ok=True)
    if stderr_log:
        stderr_log.parent.mkdir(parents=True, exist_ok=True)

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        def read_stdout():
            for line in proc.stdout:
                stdout_lines.append(line)
                if stdout_log:
                    with open(stdout_log, "a", encoding="utf-8") as f:
                        f.write(line)

        def read_stderr():
            for line in proc.stderr:
                stderr_lines.append(line)
                if stderr_log:
                    with open(stderr_log, "a", encoding="utf-8") as f:
                        f.write(line)

        t1 = threading.Thread(target=read_stdout, daemon=True)
        t2 = threading.Thread(target=read_stderr, daemon=True)
        t1.start()
        t2.start()

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            t1.join(timeout=5)
            t2.join(timeout=5)
            return RunResult(-1, "".join(stdout_lines), f"TIMEOUT after {timeout}s\n" + "".join(stderr_lines))

        t1.join(timeout=10)
        t2.join(timeout=10)
        return RunResult(proc.returncode, "".join(stdout_lines), "".join(stderr_lines))

    except FileNotFoundError as e:
        return RunResult(127, "", f"Command not found: {e}")
