from datetime import date

import pytest

from minitask.core.daily_plan_service import DailyPlanService
from minitask.core.exceptions import DuplicateDailyAssignmentError
from minitask.core.task_service import TaskService
from minitask.database import DailyPlanRepository


def test_today_tomorrow_follow_injected_calendar_date(database):
    current = [date(2026, 11, 11)]
    plans = DailyPlanService(database, today_provider=lambda: current[0])
    task = plans.create_task_for_date("Prepare release", plans.tomorrow_date())

    assert plans.get_today() == []
    assert plans.get_tomorrow() == [task]
    current[0] = date(2026, 11, 12)

    assert plans.get_today() == [task]
    assigned = DailyPlanRepository(database).list_for_date("2026-11-12")
    assert assigned[0].task_id == task.id
    assert len(DailyPlanRepository(database).list_for_date("2026-11-12")) == 1
    assert DailyPlanRepository(database).list_for_date("2026-11-13") == []


def test_long_term_task_is_assigned_by_reference_and_completion_is_shared(database):
    tasks = TaskService(database)
    plans = DailyPlanService(database, task_service=tasks)
    parent = tasks.create_task("Finish compiler")
    child = tasks.create_subtask(parent.id, "Implement lexer")
    plans.add_existing_task(child.id, "2026-11-12")

    tasks.set_completed(child.id, True)

    assert plans.list_for_date("2026-11-12")[0] == tasks.get_task(child.id)
    assert tasks.list_long_term()[1].id == child.id
    assert tasks.list_long_term()[1].is_completed is True
    assert plans.list_for_date("2026-11-12")[0].parent_id == parent.id


def test_daily_creation_is_all_or_nothing(database):
    plans = DailyPlanService(database)

    with pytest.raises(ValueError, match="ISO date"):
        plans.create_task_for_date("Will roll back", "2026-02-30")

    assert plans.tasks.list_all() == []


def test_deadline_does_not_automatically_assign_task(database):
    tasks = TaskService(database)
    plans = DailyPlanService(database)
    task = tasks.create_task("Deadline only", due_date="2026-11-12")

    assert task not in plans.list_for_date("2026-11-12")
    assert plans.get_tomorrow() == []


def test_duplicate_addition_is_rejected_and_multiple_dates_are_allowed(database):
    tasks = TaskService(database)
    plans = DailyPlanService(database)
    task = tasks.create_task("Read")
    plans.add_existing_task(task.id, "2026-11-12")

    with pytest.raises(DuplicateDailyAssignmentError):
        plans.add_existing_task(task.id, "2026-11-12")

    plans.add_existing_task(task.id, "2026-11-13")
    assert plans.list_for_date("2026-11-12") == [task]
    assert plans.list_for_date("2026-11-13") == [task]


def test_removing_plan_item_keeps_underlying_task(database):
    plans = DailyPlanService(database)
    task = plans.create_task_for_date("One day", "2026-11-12")

    plans.remove_task(task.id, "2026-11-12")

    assert plans.list_for_date("2026-11-12") == []
    assert plans.tasks.get_task(task.id) == task
    assert task in plans.tasks.list_all()


def test_daily_plan_service_reorders_tasks(database):
    plans = DailyPlanService(database)
    first = plans.create_task_for_date("First", "2026-11-12")
    second = plans.create_task_for_date("Second", "2026-11-12")

    reordered = plans.reorder("2026-11-12", [second.id, first.id])

    assert reordered == [second, first]
