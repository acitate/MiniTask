import pytest

from minitask.core.exceptions import InvalidTaskError, TaskNotFoundError
from minitask.core.task_service import TaskService


def test_create_update_and_complete_task(database):
    tasks = TaskService(database)
    task = tasks.create_task("Draft proposal")

    edited = tasks.update_task(
        task.id,
        title="Send proposal",
        notes="Email the client",
        due_date="2026-12-02",
    )
    completed = tasks.set_completed(task.id, True)
    reopened = tasks.set_completed(task.id, False)

    assert edited.id == task.id
    assert edited.title == "Send proposal"
    assert edited.notes == "Email the client"
    assert edited.due_date == "2026-12-02"
    assert completed.is_completed is True
    assert reopened.is_completed is False


def test_task_fields_can_be_cleared(database):
    tasks = TaskService(database)
    task = tasks.create_task("Task", notes="Details", due_date="2026-12-02")

    cleared = tasks.update_task(task.id, notes=None, due_date=None)

    assert cleared.notes is None
    assert cleared.due_date is None


def test_rejects_invalid_task_edits(database):
    tasks = TaskService(database)
    task = tasks.create_task("Task")

    with pytest.raises(InvalidTaskError, match="title"):
        tasks.update_task(task.id, title="  ")
    with pytest.raises(ValueError, match="ISO date"):
        tasks.update_task(task.id, due_date="next week")
    with pytest.raises(TaskNotFoundError):
        tasks.update_task(999, title="Missing")


def test_completing_parent_does_not_change_subtasks(database):
    tasks = TaskService(database)
    parent = tasks.create_task("Project")
    child = tasks.create_subtask(parent.id, "Subtask")

    tasks.set_completed(parent.id, True)

    assert tasks.get_task(parent.id).is_completed is True
    assert tasks.get_task(child.id).is_completed is False


def test_deleting_task_removes_its_subtree(database):
    tasks = TaskService(database)
    parent = tasks.create_task("Project")
    child = tasks.create_subtask(parent.id, "Subtask")

    tasks.delete_task(parent.id)

    assert tasks.list_all() == []
    with pytest.raises(TaskNotFoundError):
        tasks.get_task(child.id)
