"""Kivy-independent manual daily planning operations."""

from collections.abc import Callable
from datetime import date, timedelta

from minitask.core.models import Task
from minitask.core.task_service import TaskService
from minitask.database import DailyPlanRepository, Database


class DailyPlanService:
    """Manage date-specific references to persistent task records."""

    def __init__(
        self,
        database: Database,
        *,
        task_service: TaskService | None = None,
        today_provider: Callable[[], date] | None = None,
    ) -> None:
        self.database = database
        self.tasks = task_service or TaskService(database)
        self.repository = DailyPlanRepository(database)
        self._today_provider = today_provider or date.today

    def today_date(self) -> date:
        """Return the current local calendar date."""
        return self._today_provider()

    def tomorrow_date(self) -> date:
        return self.today_date() + timedelta(days=1)

    def get_today(self) -> list[Task]:
        return self.list_for_date(self.today_date())

    def get_tomorrow(self) -> list[Task]:
        return self.list_for_date(self.tomorrow_date())

    def list_for_date(self, plan_date: date | str) -> list[Task]:
        """Return tasks in a date's manual plan order."""
        date_text = plan_date.isoformat() if isinstance(plan_date, date) else plan_date
        items = self.repository.list_for_date(date_text)
        return [self.tasks.get_task(item.task_id) for item in items]

    def create_task_for_date(
        self,
        title: str,
        plan_date: date | str,
        *,
        notes: str | None = None,
        due_date: str | None = None,
    ) -> Task:
        """Create a daily-only task and assign it atomically to one date."""
        date_text = plan_date.isoformat() if isinstance(plan_date, date) else plan_date
        with self.database.transaction():
            task = self.tasks.create_task(
                title,
                notes=notes,
                due_date=due_date,
                is_long_term=False,
            )
            self.repository.add(task.id, date_text)
        return task

    def add_existing_task(self, task_id: int, plan_date: date | str) -> None:
        """Manually assign an existing task reference to a date."""
        date_text = plan_date.isoformat() if isinstance(plan_date, date) else plan_date
        self.tasks.get_task(task_id)
        self.repository.add(task_id, date_text)

    def remove_task(self, task_id: int, plan_date: date | str) -> None:
        """Remove only the date-specific assignment, preserving the task."""
        date_text = plan_date.isoformat() if isinstance(plan_date, date) else plan_date
        self.repository.remove(task_id, date_text)

    def reorder(self, plan_date: date | str, task_ids: list[int]) -> list[Task]:
        """Set the exact manual order for all tasks assigned to a date."""
        date_text = plan_date.isoformat() if isinstance(plan_date, date) else plan_date
        self.repository.reorder(date_text, task_ids)
        return self.list_for_date(date_text)
