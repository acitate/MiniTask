import pytest

from minitask.core.exceptions import InvalidTaskError, TaskNotFoundError
from minitask.database import TaskRepository


def test_creates_and_reads_task_with_utc_timestamps(database):
    tasks = TaskRepository(database)

    task = tasks.create(
        "  Draft proposal  ", notes="First draft", due_date="2026-12-01"
    )

    assert task.id == 1
    assert task.title == "Draft proposal"
    assert task.notes == "First draft"
    assert task.due_date == "2026-12-01"
    assert task.created_at.endswith("Z")
    assert task.updated_at == task.created_at
    assert tasks.get(task.id) == task


def test_updates_fields_without_changing_identity(database):
    tasks = TaskRepository(database)
    original = tasks.create("Plan trip")

    updated = tasks.update(
        original.id,
        title="Book tickets",
        notes="Compare train and plane",
        due_date="2026-12-02",
        is_completed=True,
    )

    assert updated.id == original.id
    assert updated.title == "Book tickets"
    assert updated.notes == "Compare train and plane"
    assert updated.due_date == "2026-12-02"
    assert updated.is_completed is True


def test_allows_clearing_optional_fields(database):
    tasks = TaskRepository(database)
    task = tasks.create("Plan trip", notes="Maybe", due_date="2026-12-02")

    cleared = tasks.update(task.id, notes=None, due_date=None)

    assert cleared.notes is None
    assert cleared.due_date is None


@pytest.mark.parametrize("title", ["", "  "])
def test_rejects_empty_titles(database, title):
    with pytest.raises(InvalidTaskError, match="title"):
        TaskRepository(database).create(title)


def test_rejects_invalid_deadline(database):
    with pytest.raises(ValueError, match="ISO date"):
        TaskRepository(database).create("Task", due_date="tomorrow")


def test_missing_parent_is_reported_as_invalid_task(database):
    with pytest.raises(InvalidTaskError):
        TaskRepository(database).create("Orphan", parent_id=1234)


def test_missing_task_operations_raise_not_found(database):
    tasks = TaskRepository(database)

    with pytest.raises(TaskNotFoundError):
        tasks.get(42)
    with pytest.raises(TaskNotFoundError):
        tasks.delete(42)


def test_parent_relationship_and_long_term_queries(database):
    tasks = TaskRepository(database)
    parent = tasks.create("Finish compiler")
    child = tasks.create("Implement lexer", parent_id=parent.id)
    daily_only = tasks.create("Buy coffee", is_long_term=False)

    assert tasks.list_children(parent.id) == [child]
    assert [task.id for task in tasks.list_long_term()] == [parent.id, child.id]
    assert [task.id for task in tasks.list_all()] == [
        parent.id,
        child.id,
        daily_only.id,
    ]


def test_deleting_parent_cascades_to_subtasks(database):
    tasks = TaskRepository(database)
    parent = tasks.create("Project")
    child = tasks.create("Subtask", parent_id=parent.id)

    tasks.delete(parent.id)

    assert tasks.list_all() == []
    with pytest.raises(TaskNotFoundError):
        tasks.get(child.id)
