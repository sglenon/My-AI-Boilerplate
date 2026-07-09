"""base.py — ExecutorAdapter abstract base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ExecutorAdapter(ABC):
    """
    Abstract base for swarm executor adapters.

    Subclasses implement available(), version(), run_task().
    """

    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        """Return True if this executor is installed and callable."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Return version string, or 'unknown' if unavailable."""
        ...

    @abstractmethod
    def run_task(
        self,
        task_dir: Path,
        worktree_dir: Path,
        config: dict,
    ) -> int:
        """
        Run the task described in task_dir/prompt.md.
        Work happens in worktree_dir.
        Returns exit code (0 = success).

        On completion, must write or update:
          task_dir/status.json
          task_dir/stdout.log
          task_dir/stderr.log
          task_dir/diff.patch   (if write task)
        """
        ...

    def doctor_check(self) -> dict:
        """Return a dict with 'ok', 'version', 'note' for doctor output."""
        if self.available():
            return {"ok": True, "version": self.version(), "note": ""}
        return {"ok": False, "version": "n/a", "note": f"{self.name} not found on PATH"}
