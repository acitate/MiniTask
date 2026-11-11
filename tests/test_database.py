import sqlite3

import pytest

from minitask.core.exceptions import DatabaseError
from minitask.database import DailyPlanRepository, Database, TaskRepository
from minitask.database.schema import SCHEMA_VERSION


def test_initializes_versioned_schema_and_enables_foreign_keys(database):
    connection = database.connection

    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert {
        row["name"] for row in connection.execute("SELECT name FROM sqlite_master")
    } >= {"tasks", "daily_plan_items"}


def test_rejects_database_from_newer_schema_version(tmp_path):
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")

    with pytest.raises(DatabaseError, match="newer than supported"):
        Database(path)


def test_transaction_rolls_back_all_statements(database):
    with pytest.raises(RuntimeError):
        with database.transaction() as connection:
            connection.execute(
                "INSERT INTO tasks (title, created_at, updated_at) "
                "VALUES (?, ?, ?)",
                ("Temporary", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
            )
            raise RuntimeError("interrupt transaction")

    assert database.connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0


def test_nested_transactions_use_savepoints(database):
    with database.transaction() as connection:
        connection.execute(
            "INSERT INTO tasks (title, created_at, updated_at) VALUES (?, ?, ?)",
            ("Keep", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        with pytest.raises(RuntimeError):
            with database.transaction() as nested:
                nested.execute(
                    "INSERT INTO tasks (title, created_at, updated_at) "
                    "VALUES (?, ?, ?)",
                    ("Discard", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
                )
                raise RuntimeError("rollback inner transaction")

    titles = [row[0] for row in database.connection.execute("SELECT title FROM tasks")]
    assert titles == ["Keep"]


def test_database_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "folder" / "minitask.sqlite3"
    database = Database(path)
    try:
        assert path.is_file()
    finally:
        database.close()


def test_tasks_relationships_and_daily_assignments_survive_reopen(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    first = Database(path)
    tasks = TaskRepository(first)
    plans = DailyPlanRepository(first)
    parent = tasks.create(
        "Finish compiler", notes="Release target", due_date="2026-12-01"
    )
    child = tasks.create("Implement lexer", parent_id=parent.id)
    plans.add(child.id, "2026-11-12")
    first.close()

    second = Database(path)
    try:
        restored_parent = TaskRepository(second).get(parent.id)
        restored_child = TaskRepository(second).get(child.id)
        restored_plan = DailyPlanRepository(second).list_for_date("2026-11-12")

        assert restored_parent.notes == "Release target"
        assert restored_parent.due_date == "2026-12-01"
        assert restored_child.parent_id == restored_parent.id
        assert [item.task_id for item in restored_plan] == [restored_child.id]
    finally:
        second.close()
