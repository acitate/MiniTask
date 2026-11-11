"""Parameterized SQLite repository operations."""

import sqlite3
from contextlib import contextmanager
from datetime import date
from itertools import count
from typing import Any

from minitask.core.exceptions import (
    DailyAssignmentNotFoundError,
    DuplicateDailyAssignmentError,
    InvalidTaskError,
    TaskNotFoundError,
)
from minitask.core.models import DailyPlanItem, Task
from minitask.database.connection import Database, utc_timestamp

_UNSET = object()
_SAVEPOINT_IDS = count(1)


def _connection(database: Database | sqlite3.Connection) -> sqlite3.Connection:
    return database.connection if isinstance(database, Database) else database


def _task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        parent_id=row["parent_id"],
        title=row["title"],
        notes=row["notes"],
        is_long_term=bool(row["is_long_term"]),
        due_date=row["due_date"],
        is_completed=bool(row["is_completed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _daily_item(row: sqlite3.Row) -> DailyPlanItem:
    return DailyPlanItem(
        id=row["id"],
        task_id=row["task_id"],
        plan_date=row["plan_date"],
        position=row["position"],
    )


def _validate_date(value: str, field: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a valid ISO date (YYYY-MM-DD).") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must use ISO format YYYY-MM-DD.")


class TaskRepository:
    """Create, read, update, and delete persistent task records."""

    def __init__(self, database: Database | sqlite3.Connection) -> None:
        self.connection = _connection(database)

    def create(
        self,
        title: str,
        *,
        parent_id: int | None = None,
        notes: str | None = None,
        is_long_term: bool = True,
        due_date: str | None = None,
        is_completed: bool = False,
    ) -> Task:
        title = title.strip()
        if not title:
            raise InvalidTaskError("Task title cannot be empty.")
        if due_date is not None:
            _validate_date(due_date, "due_date")
        now = utc_timestamp()
        try:
            cursor = self.connection.execute(
                """INSERT INTO tasks
                   (parent_id, title, notes, is_long_term, due_date,
                    is_completed, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    parent_id,
                    title,
                    notes,
                    int(is_long_term),
                    due_date,
                    int(is_completed),
                    now,
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise InvalidTaskError("Task data violates a database constraint.") from exc
        return self.get(cursor.lastrowid)

    def get(self, task_id: int) -> Task:
        row = self.connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise TaskNotFoundError(f"Task {task_id} does not exist.")
        return _task(row)

    def list_all(self) -> list[Task]:
        rows = self.connection.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        return [_task(row) for row in rows]

    def list_long_term(self) -> list[Task]:
        rows = self.connection.execute(
            "SELECT * FROM tasks WHERE is_long_term = 1 ORDER BY id"
        ).fetchall()
        return [_task(row) for row in rows]

    def list_children(self, parent_id: int) -> list[Task]:
        rows = self.connection.execute(
            "SELECT * FROM tasks WHERE parent_id = ? ORDER BY id", (parent_id,)
        ).fetchall()
        return [_task(row) for row in rows]

    def update(
        self,
        task_id: int,
        *,
        title: str | object = _UNSET,
        notes: str | None | object = _UNSET,
        parent_id: int | None | object = _UNSET,
        is_long_term: bool | object = _UNSET,
        due_date: str | None | object = _UNSET,
        is_completed: bool | object = _UNSET,
    ) -> Task:
        changes: dict[str, Any] = {}
        for field, value in (
            ("title", title),
            ("notes", notes),
            ("parent_id", parent_id),
            ("is_long_term", is_long_term),
            ("due_date", due_date),
            ("is_completed", is_completed),
        ):
            if value is not _UNSET:
                changes[field] = value
        if "title" in changes:
            if not isinstance(changes["title"], str) or not changes["title"].strip():
                raise InvalidTaskError("Task title cannot be empty.")
            changes["title"] = changes["title"].strip()
        if "due_date" in changes and changes["due_date"] is not None:
            _validate_date(changes["due_date"], "due_date")
        self.get(task_id)
        if not changes:
            return self.get(task_id)
        if "is_long_term" in changes:
            changes["is_long_term"] = int(bool(changes["is_long_term"]))
        if "is_completed" in changes:
            changes["is_completed"] = int(bool(changes["is_completed"]))
        changes["updated_at"] = utc_timestamp()
        assignments = ", ".join(f"{field} = ?" for field in changes)
        try:
            self.connection.execute(
                f"UPDATE tasks SET {assignments} WHERE id = ?",
                (*changes.values(), task_id),
            )
        except sqlite3.IntegrityError as exc:
            raise InvalidTaskError("Task data violates a database constraint.") from exc
        return self.get(task_id)

    def delete(self, task_id: int) -> None:
        cursor = self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise TaskNotFoundError(f"Task {task_id} does not exist.")


class DailyPlanRepository:
    """Store manually curated task references for calendar dates."""

    def __init__(self, database: Database | sqlite3.Connection) -> None:
        self.connection = _connection(database)
        self.database = database if isinstance(database, Database) else None

    def add(
        self, task_id: int, plan_date: str, *, position: int | None = None
    ) -> DailyPlanItem:
        _validate_date(plan_date, "plan_date")
        if position is not None and position < 0:
            raise ValueError("position cannot be negative.")
        try:
            context = (
                self.database.transaction()
                if self.database
                else _transaction(self.connection)
            )
            with context:
                if position is None:
                    row = self.connection.execute(
                        "SELECT COALESCE(MAX(position) + 1, 0) AS next_position "
                        "FROM daily_plan_items WHERE plan_date = ?",
                        (plan_date,),
                    ).fetchone()
                    position = row["next_position"]
                cursor = self.connection.execute(
                    """INSERT INTO daily_plan_items (task_id, plan_date, position)
                       VALUES (?, ?, ?)""",
                    (task_id, plan_date, position),
                )
        except sqlite3.IntegrityError as exc:
            existing = self.connection.execute(
                "SELECT 1 FROM daily_plan_items WHERE task_id = ? AND plan_date = ?",
                (task_id, plan_date),
            ).fetchone()
            if existing:
                raise DuplicateDailyAssignmentError(
                    f"Task {task_id} is already assigned to {plan_date}."
                ) from exc
            raise InvalidTaskError(
                "The assignment references a missing task or invalid position."
            ) from exc
        return self.get(cursor.lastrowid)

    def get(self, item_id: int) -> DailyPlanItem:
        row = self.connection.execute(
            "SELECT * FROM daily_plan_items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise DailyAssignmentNotFoundError(
                f"Daily plan item {item_id} does not exist."
            )
        return _daily_item(row)

    def list_for_date(self, plan_date: str) -> list[DailyPlanItem]:
        _validate_date(plan_date, "plan_date")
        rows = self.connection.execute(
            """SELECT * FROM daily_plan_items
               WHERE plan_date = ? ORDER BY position, id""",
            (plan_date,),
        ).fetchall()
        return [_daily_item(row) for row in rows]

    def remove(self, task_id: int, plan_date: str) -> None:
        _validate_date(plan_date, "plan_date")
        cursor = self.connection.execute(
            "DELETE FROM daily_plan_items WHERE task_id = ? AND plan_date = ?",
            (task_id, plan_date),
        )
        if cursor.rowcount == 0:
            raise DailyAssignmentNotFoundError(
                f"Task {task_id} is not assigned to {plan_date}."
            )

    def reorder(self, plan_date: str, task_ids: list[int]) -> list[DailyPlanItem]:
        _validate_date(plan_date, "plan_date")
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Each task can appear only once in a daily plan.")
        if self.database is not None:
            context = self.database.transaction()
        else:
            context = _transaction(self.connection)
        with context:
            items = self.list_for_date(plan_date)
            if set(task_ids) != {item.task_id for item in items}:
                raise ValueError("task_ids must contain every task in this plan once.")
            self.connection.executemany(
                "UPDATE daily_plan_items SET position = ? "
                "WHERE task_id = ? AND plan_date = ?",
                (
                    (position, task_id, plan_date)
                    for position, task_id in enumerate(task_ids)
                ),
            )
        return self.list_for_date(plan_date)


@contextmanager
def _transaction(connection: sqlite3.Connection):
    """Transaction fallback when a repository receives a raw connection."""
    nested = connection.in_transaction
    savepoint = f"minitask_sp_{next(_SAVEPOINT_IDS)}"
    try:
        connection.execute(f"SAVEPOINT {savepoint}" if nested else "BEGIN IMMEDIATE")
        yield connection
        if nested:
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        else:
            connection.commit()
    except Exception:
        if connection.in_transaction:
            if nested:
                connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            else:
                connection.rollback()
        raise
