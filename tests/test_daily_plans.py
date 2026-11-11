import pytest

from minitask.core.exceptions import (
    DailyAssignmentNotFoundError,
    DuplicateDailyAssignmentError,
    TaskNotFoundError,
)
from minitask.database import DailyPlanRepository, TaskRepository


def test_daily_assignment_references_existing_task(database):
    tasks = TaskRepository(database)
    plans = DailyPlanRepository(database)
    task = tasks.create("Implement lexer", due_date="2026-11-12")

    assignment = plans.add(task.id, "2026-11-12")

    assert assignment.task_id == task.id
    assert assignment.plan_date == "2026-11-12"
    assert assignment.position == 0
    assert tasks.get(assignment.task_id).id == task.id


def test_assignment_is_unique_per_task_and_date(database):
    task = TaskRepository(database).create("Read")
    plans = DailyPlanRepository(database)
    plans.add(task.id, "2026-11-12")

    with pytest.raises(DuplicateDailyAssignmentError):
        plans.add(task.id, "2026-11-12")

    next_day = plans.add(task.id, "2026-11-13")
    assert next_day.task_id == task.id


def test_deadline_does_not_create_assignment(database):
    task = TaskRepository(database).create("Review", due_date="2026-11-12")

    assert DailyPlanRepository(database).list_for_date("2026-11-12") == []
    assert task.due_date == "2026-11-12"


def test_removing_assignment_preserves_task(database):
    tasks = TaskRepository(database)
    plans = DailyPlanRepository(database)
    task = tasks.create("Review")
    plans.add(task.id, "2026-11-12")

    plans.remove(task.id, "2026-11-12")

    assert tasks.get(task.id) == task
    assert plans.list_for_date("2026-11-12") == []
    with pytest.raises(DailyAssignmentNotFoundError):
        plans.remove(task.id, "2026-11-12")


def test_task_delete_cascades_to_daily_assignments(database):
    tasks = TaskRepository(database)
    plans = DailyPlanRepository(database)
    task = tasks.create("Review")
    plans.add(task.id, "2026-11-12")

    tasks.delete(task.id)

    assert plans.list_for_date("2026-11-12") == []
    with pytest.raises(TaskNotFoundError):
        tasks.get(task.id)


def test_reorders_all_items_atomically(database):
    tasks = TaskRepository(database)
    plans = DailyPlanRepository(database)
    one = tasks.create("One")
    two = tasks.create("Two")
    three = tasks.create("Three")
    plans.add(one.id, "2026-11-12")
    plans.add(two.id, "2026-11-12")
    plans.add(three.id, "2026-11-12")

    items = plans.reorder("2026-11-12", [three.id, one.id, two.id])

    assert [item.task_id for item in items] == [three.id, one.id, two.id]
    assert [item.position for item in items] == [0, 1, 2]


def test_reorder_rejects_partial_or_duplicate_order(database):
    tasks = TaskRepository(database)
    plans = DailyPlanRepository(database)
    one = tasks.create("One")
    two = tasks.create("Two")
    plans.add(one.id, "2026-11-12")
    plans.add(two.id, "2026-11-12")

    with pytest.raises(ValueError, match="every task"):
        plans.reorder("2026-11-12", [one.id])
    with pytest.raises(ValueError, match="once"):
        plans.reorder("2026-11-12", [one.id, one.id])

    assert [item.task_id for item in plans.list_for_date("2026-11-12")] == [
        one.id,
        two.id,
    ]


def test_rejects_invalid_plan_dates(database):
    task = TaskRepository(database).create("One")
    with pytest.raises(ValueError, match="ISO date"):
        DailyPlanRepository(database).add(task.id, "2026-02-30")
