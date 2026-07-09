"""test_prompt_revision.py — render_prompt with revision fields."""
import pytest
from pathlib import Path
from lib.tasks import render_prompt


TEMPLATE_CONTENT = """# Task
run_id: {{run_id}}
task_id: {{task_id}}
repo: {{repo}}
base_branch: {{base_branch}}
worktree: {{worktree}}
executor: {{executor}}
goal: {{goal}}
context: {{context}}
files_in_scope: {{files_in_scope}}
files_out_of_scope: {{files_out_of_scope}}
validation_command: {{validation_command}}
task_dir: {{task_dir}}

## Prior Attempt (rejected)
{{prior_attempt}}

## Required Fixes (from reviewer)
{{fix_instructions}}
"""


def _render(tmp_path, prior_attempt="", fix_instructions=""):
    template_path = tmp_path / "template.md"
    template_path.write_text(TEMPLATE_CONTENT, encoding="utf-8")
    task_dir = tmp_path / "task"
    task_dir.mkdir()

    prompt_path = render_prompt(
        template_path=template_path,
        task_dir=task_dir,
        run_id="run-001",
        task_id="T001",
        repo="myrepo",
        base_branch="main",
        worktree="/tmp/wt",
        executor="codex",
        goal="fix bug",
        context="some context",
        files_in_scope=["src/main.py"],
        files_out_of_scope=[".env"],
        validation_command="pytest",
        prior_attempt=prior_attempt,
        fix_instructions=fix_instructions,
    )
    return prompt_path.read_text(encoding="utf-8")


def test_render_with_fix_instructions(tmp_path):
    text = _render(tmp_path, prior_attempt="prior diff: path/to/diff.patch", fix_instructions="Fix the null pointer on line 42")
    assert "Fix the null pointer on line 42" in text
    assert "prior diff: path/to/diff.patch" in text


def test_render_with_prior_attempt(tmp_path):
    text = _render(tmp_path, prior_attempt="Parent task: T001\n\nPrior summary:\nDid some stuff", fix_instructions="Add error handling")
    assert "Parent task: T001" in text
    assert "Add error handling" in text


def test_render_unset_defaults_to_none_first_attempt(tmp_path):
    text = _render(tmp_path)  # no prior_attempt, no fix_instructions
    assert "(none — first attempt)" in text
    # Should appear twice (once for prior_attempt, once for fix_instructions)
    assert text.count("(none — first attempt)") == 2


def test_render_empty_strings_default_to_none_first_attempt(tmp_path):
    text = _render(tmp_path, prior_attempt="", fix_instructions="")
    assert "(none — first attempt)" in text


def test_render_fix_instructions_replaces_placeholder(tmp_path):
    text = _render(tmp_path, fix_instructions="You must handle the edge case where input is None.")
    assert "{{fix_instructions}}" not in text
    assert "You must handle the edge case where input is None." in text


def test_render_prior_attempt_replaces_placeholder(tmp_path):
    text = _render(tmp_path, prior_attempt="See diff at /path/to/diff.patch")
    assert "{{prior_attempt}}" not in text
    assert "See diff at /path/to/diff.patch" in text
