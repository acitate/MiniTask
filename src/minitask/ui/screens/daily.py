"""Shared Today and Tomorrow task-plan screen."""

import logging
from datetime import date

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from minitask.core.daily_plan_service import DailyPlanService
from minitask.core.exceptions import MiniTaskError
from minitask.core.models import Task
from minitask.core.task_service import TaskService
from minitask.ui.theme import Theme
from minitask.ui.widgets.task_dialogs import TaskTitleDialog
from minitask.ui.widgets.task_item import TaskItem
from minitask.ui.widgets.task_picker import TaskPicker
from minitask.ui.widgets.text import align_label

logger = logging.getLogger(__name__)


class DailyPlanScreen(Screen):
    """Date-specific task list with manual add, remove, and reorder actions."""

    def __init__(
        self,
        name: str,
        title: str,
        task_service: TaskService,
        plan_service: DailyPlanService,
        theme: Theme,
        shell,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.title = title
        self.tasks = task_service
        self.plans = plan_service
        self.theme = theme
        self.shell = shell
        self.current_tasks: list[Task] = []
        self._draw_background()

        page = BoxLayout(
            orientation="vertical",
            padding=dp(theme.page_padding),
            spacing=dp(theme.section_spacing),
        )
        header = BoxLayout(
            size_hint_y=None, height=dp(theme.touch_target), spacing=dp(theme.spacing)
        )
        header.add_widget(
            align_label(Label(
                text=title,
                color=theme.color("text"),
                font_size=sp(26),
                bold=True,
                halign="left",
            ))
        )
        self.add_button = Button(
            text="+",
            size_hint_x=None,
            width=dp(theme.touch_target),
            background_normal="",
            background_color=theme.color("accent"),
            color=theme.color("on_accent"),
            font_size=sp(23),
        )
        self.add_button.bind(on_release=lambda *_: self._open_new_task())
        header.add_widget(self.add_button)
        page.add_widget(header)

        existing = Button(
            text="Add existing task",
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=theme.color("elevated"),
            color=theme.color("accent"),
            font_size=sp(15),
        )
        existing.bind(on_release=lambda *_: self._open_picker())
        page.add_widget(existing)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.task_container = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(7)
        )
        self.task_container.bind(
            minimum_height=self.task_container.setter("height")
        )
        scroll.add_widget(self.task_container)
        page.add_widget(scroll)
        self.status = align_label(Label(
            text="",
            size_hint_y=None,
            height=dp(22),
            color=theme.color("destructive"),
            font_size=sp(12),
            halign="left",
        ))
        page.add_widget(self.status)
        self.add_widget(page)

    def _draw_background(self) -> None:
        with self.canvas.before:
            Color(*self.theme.color("window"))
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda _widget, value: setattr(self._background, "pos", value),
            size=lambda _widget, value: setattr(self._background, "size", value),
        )

    def target_date(self) -> date:
        raise NotImplementedError

    def on_pre_enter(self, *_args) -> None:
        self.refresh()

    def refresh(self) -> None:
        try:
            self.current_tasks = self.plans.list_for_date(self.target_date())
            self._render_tasks()
            self.status.text = ""
        except Exception as exc:
            logger.exception("Could not load the %s plan", self.title)
            self.show_error(exc)

    def _render_tasks(self) -> None:
        self.task_container.clear_widgets()
        if not self.current_tasks:
            self.task_container.add_widget(
                Label(
                    text=f"Nothing planned for {self.title.lower()} yet.",
                    size_hint_y=None,
                    height=dp(90),
                    color=self.theme.color("secondary"),
                    font_size=sp(15),
                )
            )
            return
        for task in self.current_tasks:
            self.task_container.add_widget(
                TaskItem(
                    task,
                    self.theme,
                    on_complete=self._set_completed,
                    on_open=lambda selected: self.shell.open_details(selected.id),
                    on_move=lambda direction, selected=task: self._move(
                        selected.id, direction
                    ),
                    on_remove=self._remove,
                )
            )

    def _open_new_task(self) -> None:
        dialog = TaskTitleDialog(
            self.theme,
            lambda title: self._create_task(title),
            heading=f"New {self.title.lower()} task",
        )
        dialog.open()

    def _create_task(self, title: str) -> None:
        try:
            self.plans.create_task_for_date(title, self.target_date())
            self.refresh()
        except Exception as exc:
            logger.exception("Could not create a task in the %s plan", self.title)
            self.show_error(exc)

    def _open_picker(self) -> None:
        try:
            existing_ids = {task.id for task in self.current_tasks}
            picker = TaskPicker(
                self.tasks,
                self.theme,
                lambda task_id: self._add_existing(task_id),
                excluded_ids=existing_ids,
            )
            picker.open()
        except Exception as exc:
            logger.exception("Could not open the task picker")
            self.show_error(exc)

    def _add_existing(self, task_id: int) -> None:
        try:
            self.plans.add_existing_task(task_id, self.target_date())
            self.refresh()
        except Exception as exc:
            logger.exception("Could not add a task to the %s plan", self.title)
            self.show_error(exc)

    def _set_completed(self, task: Task, completed: bool) -> None:
        try:
            self.tasks.set_completed(task.id, completed)
            self.refresh()
            self.shell.refresh_task_views()
        except Exception as exc:
            logger.exception("Could not update task completion")
            self.show_error(exc)

    def _move(self, task_id: int, direction: int) -> None:
        try:
            ordered_ids = [task.id for task in self.current_tasks]
            index = ordered_ids.index(task_id)
            target = index + direction
            if not 0 <= target < len(ordered_ids):
                return
            ordered_ids[index], ordered_ids[target] = (
                ordered_ids[target],
                ordered_ids[index],
            )
            self.plans.reorder(self.target_date(), ordered_ids)
            self.refresh()
        except Exception as exc:
            logger.exception("Could not reorder the %s plan", self.title)
            self.show_error(exc)

    def _remove(self, task: Task) -> None:
        try:
            self.plans.remove_task(task.id, self.target_date())
            self.refresh()
        except Exception as exc:
            logger.exception("Could not remove a task from the %s plan", self.title)
            self.show_error(exc)

    def show_error(self, error: Exception) -> None:
        self.status.text = (
            str(error)
            if isinstance(error, MiniTaskError)
            else "Couldn't update this plan. Please try again."
        )


class TodayScreen(DailyPlanScreen):
    def __init__(self, task_service, plan_service, theme, shell, **kwargs) -> None:
        super().__init__(
            "today", "Today", task_service, plan_service, theme, shell, **kwargs
        )

    def target_date(self) -> date:
        return self.plans.today_date()


class TomorrowScreen(DailyPlanScreen):
    def __init__(self, task_service, plan_service, theme, shell, **kwargs) -> None:
        super().__init__(
            "tomorrow", "Tomorrow", task_service, plan_service, theme, shell, **kwargs
        )

    def target_date(self) -> date:
        return self.plans.tomorrow_date()
