#!/usr/bin/env python3
"""Install the bundled Spec-Driven runtime into a repository without overwrites."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


REQUIRED_FILES = (
    ".specify/scripts/python/common.py",
    ".specify/scripts/python/check_prerequisites.py",
    ".specify/scripts/python/create_new_feature.py",
    ".specify/scripts/python/resolve_template.py",
    ".specify/scripts/python/setup_plan.py",
    ".specify/scripts/python/setup_tasks.py",
    ".specify/templates/spec-template.md",
    ".specify/templates/plan-template.md",
    ".specify/templates/tasks-template.md",
    ".specify/templates/checklist-template.md",
    ".specify/templates/constitution-template.md",
    ".specify/memory/constitution.md",
)


def readiness(project_root: Path) -> tuple[bool, list[str]]:
    missing = [path for path in REQUIRED_FILES if not (project_root / path).is_file()]
    return not missing, missing


def copy_missing(source_root: Path, project_root: Path) -> list[str]:
    created: list[str] = []
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        destination = project_root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        created.append(relative.as_posix())
    return created


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize the self-contained Spec-Driven project runtime."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to initialize (default: current directory).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check readiness without creating files.",
    )
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve()
    source_root = Path(__file__).resolve().parent.parent / "assets" / "project"

    if not project_root.is_dir():
        parser.error(f"project root is not a directory: {project_root}")
    if not source_root.is_dir():
        print(json.dumps({"ready": False, "error": f"missing bundled runtime: {source_root}"}))
        return 2

    created = [] if args.check else copy_missing(source_root, project_root)
    ready, missing = readiness(project_root)
    print(
        json.dumps(
            {
                "project_root": str(project_root),
                "mode": "check" if args.check else "initialize",
                "created": created,
                "created_count": len(created),
                "missing": missing,
                "ready": ready,
            },
            indent=2,
        )
    )
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
