"""Compact, reusable task row widget."""

from collections.abc import Callable

from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label

from minitask.core.models import Task
from minitask.ui.theme import Theme


def _button(
    text: str,
    theme: Theme,
    callback: Callable,
    *,
    color: str = "secondary",
    width: int = 42,
) -> Button:
    button = Button(
        text=text,
        size_hint_x=None,
        width=dp(width),
        background_normal="",
        background_down="",
        background_color=(0, 0, 0, 0),
        color=theme.color(color),
        font_size=sp(16),
    )
    button.bind(on_release=lambda *_: callback())
    return button


class TaskItem(BoxLayout):
    """Task completion, detail access, and optional hierarchy/order actions."""

    def __init__(
        self,
        task: Task,
        theme: Theme,
        *,
        depth: int = 0,
        expanded: bool = True,
        on_complete: Callable[[Task, bool], None],
        on_open: Callable[[Task], None],
        on_toggle: Callable[[Task], None] | None = None,
        on_move: Callable[[int], None] | None = None,
        on_remove: Callable[[Task], None] | None = None,
        on_add_subtask: Callable[[Task], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(theme.row_height),
            spacing=dp(4),
            padding=(dp(8 + depth * 16), dp(4)),
            **kwargs,
        )
        self.task = task
        self.theme = theme
        with self.canvas.before:
            self._background_color = Color(*theme.color("card"))
            self._background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(theme.corner_radius)],
            )
            self._border_color = Color(*theme.color("border"))
            self._border = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(theme.corner_radius),
                ),
                width=dp(0.7),
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        self.checkbox = CheckBox(
            active=task.is_completed,
            size_hint_x=None,
            width=dp(44),
            color=theme.color("accent"),
        )
        self.checkbox.bind(
            active=lambda _checkbox, value: on_complete(task, value)
        )
        self.add_widget(self.checkbox)

        if on_toggle is not None:
            self.add_widget(
                _button("v" if expanded else ">", theme, lambda: on_toggle(task))
            )

        title = task.title + ("  ✓" if task.is_completed else "")
        self.title_button = Button(
            text=title,
            halign="left",
            valign="middle",
            size_hint_x=1,
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=theme.color("secondary" if task.is_completed else "text"),
            font_size=sp(16),
            shorten=True,
            shorten_from="right",
        )
        self.title_button.bind(size=self._fit_title)
        self.title_button.bind(on_release=lambda *_: on_open(task))
        self.add_widget(self.title_button)

        if task.due_date:
            self.add_widget(
                Label(
                    text=task.due_date,
                    size_hint_x=None,
                    width=dp(70),
                    color=theme.color("secondary"),
                    font_size=sp(10),
                    halign="right",
                    valign="middle",
                )
            )
        if on_move is not None:
            self.add_widget(
                _button("^", theme, lambda: on_move(-1), width=theme.compact_action)
            )
            self.add_widget(
                _button("v", theme, lambda: on_move(1), width=theme.compact_action)
            )
        if on_remove is not None:
            self.add_widget(
                _button(
                    "×",
                    theme,
                    lambda: on_remove(task),
                    color="destructive",
                    width=theme.compact_action,
                )
            )
        if on_add_subtask is not None:
            self.add_widget(
                _button("+", theme, lambda: on_add_subtask(task), color="accent")
            )

    def _fit_title(self, button: Button, size: tuple[float, float]) -> None:
        button.text_size = size

    def _update_canvas(self, *_args) -> None:
        self._background.pos = self.pos
        self._background.size = self.size
        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(self.theme.corner_radius),
        )
