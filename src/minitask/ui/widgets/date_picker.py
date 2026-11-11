"""A small month-calendar date picker built from native Kivy buttons."""

import calendar
from collections.abc import Callable
from datetime import date

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView

from minitask.ui.theme import Theme
from minitask.ui.widgets.task_dialogs import styled_button


class CalendarPicker(ModalView):
    """Choose a calendar date, or clear the optional deadline."""

    def __init__(
        self,
        theme: Theme,
        on_select: Callable[[str | None], None],
        initial_date: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            size_hint=(0.94, None),
            height=dp(480),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        self.theme = theme
        self.on_select = on_select
        try:
            selected = (
                date.fromisoformat(initial_date) if initial_date else date.today()
            )
        except ValueError:
            selected = date.today()
        self.year = selected.year
        self.month = selected.month

        self.card = BoxLayout(
            orientation="vertical", padding=dp(16), spacing=dp(8)
        )
        with self.card.canvas.before:
            Color(*theme.color("card"))
            self._background = RoundedRectangle(
                pos=self.card.pos,
                size=self.card.size,
                radius=[dp(theme.corner_radius + 4)],
            )
        self.card.bind(
            pos=lambda widget, value: setattr(self._background, "pos", value),
            size=lambda widget, value: setattr(self._background, "size", value),
        )
        self.header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        previous = self._arrow("‹", lambda: self._shift_month(-1))
        self.month_label = Label(
            color=theme.color("text"), font_size=sp(18), halign="center"
        )
        following = self._arrow("›", lambda: self._shift_month(1))
        self.header.add_widget(previous)
        self.header.add_widget(self.month_label)
        self.header.add_widget(following)
        self.card.add_widget(self.header)
        self.grid = GridLayout(cols=7, rows=7, spacing=dp(2), size_hint_y=None)
        self.grid.height = dp(7 * 42)
        self.card.add_widget(self.grid)
        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        clear = styled_button("Clear deadline", theme)
        clear.bind(on_release=lambda *_: self._choose(None))
        cancel = styled_button("Cancel", theme)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(clear)
        actions.add_widget(cancel)
        self.card.add_widget(actions)
        self.add_widget(self.card)
        self._render_month()

    def _arrow(self, text: str, callback: Callable[[], None]) -> Button:
        button = Button(
            text=text,
            size_hint_x=None,
            width=dp(48),
            background_normal="",
            background_color=self.theme.color("elevated"),
            color=self.theme.color("text"),
            font_size=sp(24),
        )
        button.bind(on_release=lambda *_: callback())
        return button

    def _shift_month(self, amount: int) -> None:
        month_index = self.year * 12 + self.month - 1 + amount
        self.year, month = divmod(month_index, 12)
        self.month = month + 1
        self._render_month()

    def _render_month(self) -> None:
        self.month_label.text = f"{calendar.month_name[self.month]} {self.year}"
        self.grid.clear_widgets()
        for weekday in ("M", "T", "W", "T", "F", "S", "S"):
            self.grid.add_widget(
                Label(
                    text=weekday,
                    color=self.theme.color("secondary"),
                    font_size=sp(12),
                )
            )
        first_weekday, days_in_month = calendar.monthrange(self.year, self.month)
        day_values: list[int | None] = [None] * first_weekday
        day_values.extend(range(1, days_in_month + 1))
        day_values.extend([None] * (42 - len(day_values)))
        for day in day_values:
            if day is None:
                self.grid.add_widget(Label(text=""))
                continue
            button = Button(
                text=str(day),
                background_normal="",
                background_down="",
                background_color=self.theme.color("elevated"),
                color=self.theme.color("text"),
                font_size=sp(14),
            )
            button.bind(
                on_release=lambda _button, picked=day: self._choose(
                    date(self.year, self.month, picked).isoformat()
                )
            )
            self.grid.add_widget(button)

    def _choose(self, value: str | None) -> None:
        self.on_select(value)
        self.dismiss()
