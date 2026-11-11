"""Immutable domain representations returned by the database layer."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Task:
    """A single persistent task, optionally nested under another task."""

    id: int
    parent_id: int | None
    title: str
    notes: str | None
    is_long_term: bool
    due_date: str | None
    is_completed: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class DailyPlanItem:
    """A reference to a task in one calendar day's manually ordered plan."""

    id: int
    task_id: int
    plan_date: str
    position: int


@dataclass(frozen=True, slots=True)
class TaskTreeNode:
    """A task and its visible children for hierarchical views."""

    task: Task
    children: tuple["TaskTreeNode", ...] = ()
