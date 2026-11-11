"""Hierarchical list shared by Long-term and All screens."""

import logging

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from minitask.core.exceptions import MiniTaskError
from minitask.core.models import Task, TaskTreeNode
from minitask.core.task_service import TaskService
from minitask.ui.theme import Theme
from minitask.ui.widgets.task_dialogs import TaskTitleDialog
from minitask.ui.widgets.task_item import TaskItem
from minitask.ui.widgets.text import align_label

logger = logging.getLogger(__name__)


class TaskTreeScreen(Screen):
    """Display a collapsible hierarchy of persistent task records."""

    def __init__(
        self,
        name: str,
        title: str,
        tasks: TaskService,
        theme: Theme,
        shell,
        *,
        long_term_only: bool,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.title = title
        self.tasks = tasks
        self.theme = theme
        self.shell = shell
        self.long_term_only = long_term_only
        self.expanded: set[int] | None = None
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
        if long_term_only:
            add = Button(
                text="+",
                size_hint_x=None,
                width=dp(theme.touch_target),
                background_normal="",
                background_color=theme.color("accent"),
                color=theme.color("on_accent"),
                font_size=sp(23),
            )
            add.bind(on_release=lambda *_: self._new_task())
            header.add_widget(add)
        page.add_widget(header)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.task_container = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(7)
        )
        self.task_container.bind(
            minimum_height=self.task_container.setter("height")
        )
        self.scroll.add_widget(self.task_container)
        page.add_widget(self.scroll)
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

    def on_pre_enter(self, *_args) -> None:
        self.refresh()

    def refresh(self) -> None:
        try:
            roots = self.tasks.tree(long_term_only=self.long_term_only)
            if self.expanded is None:
                self.expanded = {
                    node.task.id for node in self._walk(roots) if node.children
                }
            self.task_container.clear_widgets()
            if not roots:
                self.task_container.add_widget(
                    Label(
                        text=(
                            "No long-term tasks yet."
                            if self.long_term_only
                            else "No tasks yet."
                        ),
                        size_hint_y=None,
                        height=dp(90),
                        color=self.theme.color("secondary"),
                        font_size=sp(15),
                    )
                )
            else:
                for node in roots:
                    self._append_node(node, depth=0)
            self.status.text = ""
        except Exception as exc:
            logger.exception("Could not load the %s task list", self.title)
            self.show_error(exc)

    def _append_node(self, node: TaskTreeNode, depth: int) -> None:
        task = node.task
        self.task_container.add_widget(
            TaskItem(
                task,
                self.theme,
                depth=depth,
                expanded=task.id in self.expanded,
                on_complete=self._set_completed,
                on_open=lambda selected: self.shell.open_details(selected.id),
                on_toggle=(
                    lambda _selected, task_id=task.id: self._toggle(task_id)
                )
                if node.children
                else None,
                on_add_subtask=self._new_subtask if self.long_term_only else None,
            )
        )
        if task.id in self.expanded:
            for child in node.children:
                self._append_node(child, depth + 1)

    def _toggle(self, task_id: int) -> None:
        if task_id in self.expanded:
            self.expanded.remove(task_id)
        else:
            self.expanded.add(task_id)
        self.refresh()

    def _set_completed(self, task: Task, completed: bool) -> None:
        try:
            self.tasks.set_completed(task.id, completed)
            self.refresh()
            self.shell.refresh_task_views()
        except Exception as exc:
            logger.exception("Could not update task completion")
            self.show_error(exc)

    def _new_task(self) -> None:
        dialog = TaskTitleDialog(
            self.theme,
            lambda title: self._create_task(title),
            heading="New long-term task",
        )
        dialog.open()

    def _create_task(self, title: str) -> None:
        try:
            task = self.tasks.create_task(title, is_long_term=True)
            if self.expanded is not None:
                self.expanded.add(task.id)
            self.refresh()
        except Exception as exc:
            logger.exception("Could not create a task")
            self.show_error(exc)

    def _new_subtask(self, parent: Task) -> None:
        dialog = TaskTitleDialog(
            self.theme,
            lambda title: self._create_subtask(parent.id, title),
            heading="New subtask",
        )
        dialog.open()

    def _create_subtask(self, parent_id: int, title: str) -> None:
        try:
            self.tasks.create_subtask(parent_id, title)
            if self.expanded is not None:
                self.expanded.add(parent_id)
            self.refresh()
        except Exception as exc:
            logger.exception("Could not create a subtask")
            self.show_error(exc)

    def show_error(self, error: Exception) -> None:
        self.status.text = (
            str(error)
            if isinstance(error, MiniTaskError)
            else "Couldn't update this task list. Please try again."
        )

    @staticmethod
    def _walk(nodes: list[TaskTreeNode]):
        for node in nodes:
            yield node
            yield from TaskTreeScreen._walk(list(node.children))
