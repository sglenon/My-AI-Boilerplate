"""test_tasks_revision.py — round-trip tests for parse_task_id, revision_task_id, latest_revision."""
import pytest
from pathlib import Path
from lib.tasks import parse_task_id, revision_task_id, latest_revision


# ---------------------------------------------------------------------------
# parse_task_id
# ---------------------------------------------------------------------------

def test_parse_plain():
    assert parse_task_id("T001") == ("T001", 1)


def test_parse_rev2():
    assert parse_task_id("T001-r2") == ("T001", 2)


def test_parse_rev11():
    assert parse_task_id("T010-r11") == ("T010", 11)


def test_parse_large_rev():
    assert parse_task_id("T005-r100") == ("T005", 100)


def test_parse_malformed_no_crash():
    # Has -r prefix but no digits after — should not crash; return as-is rev=1
    result = parse_task_id("T001-rabc")
    assert result == ("T001-rabc", 1)


def test_parse_empty_string_no_crash():
    result = parse_task_id("")
    assert result == ("", 1)


# ---------------------------------------------------------------------------
# revision_task_id
# ---------------------------------------------------------------------------

def test_revision_task_id_rev1():
    # rev=1 returns base only (no suffix)
    assert revision_task_id("T001", 1) == "T001"


def test_revision_task_id_rev2():
    assert revision_task_id("T001", 2) == "T001-r2"


def test_revision_task_id_rev11():
    assert revision_task_id("T010", 11) == "T010-r11"


def test_roundtrip_rev2():
    base, rev = parse_task_id("T001-r2")
    assert revision_task_id(base, rev) == "T001-r2"


def test_roundtrip_rev11():
    base, rev = parse_task_id("T010-r11")
    assert revision_task_id(base, rev) == "T010-r11"


def test_roundtrip_plain():
    base, rev = parse_task_id("T001")
    assert revision_task_id(base, rev) == "T001"


# ---------------------------------------------------------------------------
# latest_revision
# ---------------------------------------------------------------------------

def _make_tasks_dir(tmp_path: Path, names: list) -> Path:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for name in names:
        (tasks_dir / name).mkdir()
    return tasks_dir


def test_latest_revision_only_base(tmp_path):
    tasks_dir = _make_tasks_dir(tmp_path, ["T001"])
    d, rev = latest_revision(tasks_dir, "T001")
    assert rev == 1
    assert d is not None
    assert d.name == "T001"


def test_latest_revision_with_r2(tmp_path):
    tasks_dir = _make_tasks_dir(tmp_path, ["T001", "T001-r2"])
    d, rev = latest_revision(tasks_dir, "T001")
    assert rev == 2
    assert d.name == "T001-r2"


def test_latest_revision_int_sort_not_lexical(tmp_path):
    # Lexical sort: T001-r10 < T001-r2, but integer sort: T001-r2 < T001-r10
    tasks_dir = _make_tasks_dir(tmp_path, ["T001", "T001-r2", "T001-r10"])
    d, rev = latest_revision(tasks_dir, "T001")
    assert rev == 10
    assert d.name == "T001-r10"


def test_latest_revision_no_match(tmp_path):
    tasks_dir = _make_tasks_dir(tmp_path, ["T002", "T003"])
    d, rev = latest_revision(tasks_dir, "T001")
    assert d is None
    assert rev == 0


def test_latest_revision_nonexistent_dir(tmp_path):
    tasks_dir = tmp_path / "tasks_does_not_exist"
    d, rev = latest_revision(tasks_dir, "T001")
    assert d is None
    assert rev == 0


def test_latest_revision_ignores_other_tasks(tmp_path):
    tasks_dir = _make_tasks_dir(tmp_path, ["T001", "T001-r2", "T002", "T002-r5"])
    d, rev = latest_revision(tasks_dir, "T001")
    assert rev == 2
    assert d.name == "T001-r2"
