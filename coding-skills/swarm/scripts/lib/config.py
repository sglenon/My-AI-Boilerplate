"""config.py — load and merge swarm configuration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GLOBAL_CONFIG_PATH = Path.home() / ".claude" / "swarm" / "config.json"

DEFAULTS: dict[str, Any] = {
    "version": 1,
    "default_parallelism": 3,
    "max_parallelism": 5,
    "max_revisions": 3,
    "require_worktrees_for_writes": True,
    "default_timeout_minutes": 45,
    "protected_globs": [
        ".env",
        ".env.*",
        "**/*secret*",
        "**/*credential*",
        "**/id_rsa",
        "**/id_ed25519",
        "**/node_modules/**",
        "**/.git/**",
    ],
    "executors": {
        "codex-gpt5.5": {
            "enabled": True,
            "adapter": "codex",
            "model": "gpt-5.5",
            "effort": "medium",
            "write_allowed": True,
            "max_parallel": 3,
        },
        "deepseek-v4-flash": {
            "enabled": True,
            "adapter": "opencode",
            "model": "opencode/deepseek-v4-flash-free",
            "effort": "medium",
            "write_allowed": False,
            "max_parallel": 3,
        },
        "sonnet": {
            "enabled": True,
            "adapter": "sonnet",
            "model": "sonnet",
            "effort": "medium",
            "write_allowed": True,
            "max_parallel": 2,
        },
        "codex-5.4-mini": {
            "enabled": False,
            "_note": "UNAVAILABLE in this environment. PLAN.md label only. Alias of gpt-5.5 which is the real model.",
            "adapter": "codex",
            "model": "gpt-5.5",
        },
        "codex-5.4": {
            "enabled": False,
            "_note": "UNAVAILABLE in this environment. PLAN.md label only. Alias of gpt-5.5 which is the real model.",
            "adapter": "codex",
            "model": "gpt-5.5",
        },
    },
}


def load_global_config() -> dict[str, Any]:
    """Load global config.json, fall back to defaults if missing."""
    if GLOBAL_CONFIG_PATH.exists():
        try:
            data = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            return _merge(DEFAULTS, data)
        except Exception:
            pass
    return dict(DEFAULTS)


def load_repo_config(repo_root: Path) -> dict[str, Any]:
    """Load .claude/swarm.config.json from repo root. Return empty dict if missing."""
    repo_cfg_path = repo_root / ".claude" / "swarm.config.json"
    if repo_cfg_path.exists():
        try:
            return json.loads(repo_cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def load_config(repo_root: Path | None = None) -> dict[str, Any]:
    """Load and merge global + repo config."""
    cfg = load_global_config()
    if repo_root:
        repo_cfg = load_repo_config(repo_root)
        cfg = _merge(cfg, repo_cfg)
    return cfg


def _merge(base: dict, override: dict) -> dict:
    """Shallow merge: override keys take precedence at top level."""
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _merge(result[k], v)
        else:
            result[k] = v
    return result
