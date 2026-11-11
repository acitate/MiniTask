"""Hierarchical picker for assigning an existing task to a day."""

from collections.abc import Callable

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView

from minitask.core.models import TaskTreeNode
from minitask.core.task_service import TaskService
from minitask.ui.theme import Theme
from minitask.ui.widgets.text import align_label


def _flatten(nodes: list[TaskTreeNode], depth: int = 0):
    for node in nodes:
        yield node.task, depth
        yield from _flatten(list(node.children), depth + 1)


class TaskPicker(ModalView):
    """Let the user choose one task while preserving parent-child context."""

    def __init__(
        self,
        tasks: TaskService,
        theme: Theme,
        on_select: Callable[[int], None],
        *,
        excluded_ids: set[int] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            size_hint=(0.94, 0.84),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        self.on_select = on_select
        excluded_ids = excluded_ids or set()
        card = BoxLayout(
            orientation="vertical", padding=dp(16), spacing=dp(10)
        )
        with card.canvas.before:
            Color(*theme.color("card"))
            background = RoundedRectangle(
                pos=card.pos,
                size=card.size,
                radius=[dp(theme.corner_radius + 4)],
            )
        card.bind(
            pos=lambda widget, value: setattr(background, "pos", value),
            size=lambda widget, value: setattr(background, "size", value),
        )
        header = BoxLayout(size_hint_y=None, height=dp(48))
        header.add_widget(
            align_label(Label(
                text="Add an existing task",
                color=theme.color("text"),
                font_size=sp(19),
                halign="left",
            ))
        )
        close = Button(
            text="×",
            size_hint_x=None,
            width=dp(44),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=theme.color("secondary"),
            font_size=sp(24),
        )
        close.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(close)
        card.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        self.rows = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(4)
        )
        self.rows.bind(minimum_height=self.rows.setter("height"))
        visible = [
            (task, depth)
            for task, depth in _flatten(tasks.tree())
            if task.id not in excluded_ids
        ]
        for task, depth in visible:
            row = align_label(Button(
                text=("  " * depth) + ("- " if depth else "") + task.title,
                size_hint_y=None,
                height=dp(50),
                halign="left",
                background_normal="",
                background_down="",
                background_color=(0, 0, 0, 0),
                color=theme.color("text"),
                font_size=sp(15),
                shorten=True,
            ))
            row.bind(on_release=lambda _button, task_id=task.id: self._select(task_id))
            self.rows.add_widget(row)
        if not visible:
            self.rows.add_widget(
                Label(
                    text="There are no tasks available to add.",
                    size_hint_y=None,
                    height=dp(60),
                    color=theme.color("secondary"),
                )
            )
        scroll.add_widget(self.rows)
        card.add_widget(scroll)
        self.add_widget(card)

    def _select(self, task_id: int) -> None:
        self.on_select(task_id)
        self.dismiss()
