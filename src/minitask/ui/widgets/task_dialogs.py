"""Small native Kivy dialogs for quick task creation and confirmation."""

from collections.abc import Callable

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput

from minitask.ui.theme import Theme
from minitask.ui.widgets.text import align_label


def styled_button(text: str, theme: Theme, *, primary: bool = False) -> Button:
    return Button(
        text=text,
        size_hint_y=None,
        height=dp(48),
        background_normal="",
        background_down="",
        background_color=theme.color("accent") if primary else theme.color("elevated"),
        color=theme.color("on_accent") if primary else theme.color("text"),
        font_size=sp(15),
    )


class TaskTitleDialog(ModalView):
    """Create a task with just its required title."""

    def __init__(
        self,
        theme: Theme,
        on_create: Callable[[str], None],
        *,
        heading: str = "New task",
        **kwargs,
    ) -> None:
        super().__init__(
            size_hint=(0.9, None),
            height=dp(240),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        self.theme = theme
        self.on_create = on_create
        card = BoxLayout(
            orientation="vertical", padding=dp(20), spacing=dp(12)
        )
        with card.canvas.before:
            Color(*theme.color("card"))
            self._background = RoundedRectangle(
                pos=card.pos,
                size=card.size,
                radius=[dp(theme.corner_radius + 4)],
            )
        card.bind(
            pos=lambda widget, value: setattr(self._background, "pos", value),
            size=lambda widget, value: setattr(self._background, "size", value),
        )
        card.add_widget(
            align_label(Label(
                text=heading,
                size_hint_y=None,
                height=dp(32),
                color=theme.color("text"),
                font_size=sp(20),
                halign="left",
                text_size=(None, None),
            ))
        )
        self.title_input = TextInput(
            hint_text="Task title",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            padding=(dp(12), dp(12)),
            background_normal="",
            background_active="",
            background_color=theme.color("elevated"),
            foreground_color=theme.color("text"),
            cursor_color=theme.color("accent"),
            hint_text_color=theme.color("secondary"),
            font_size=sp(16),
        )
        card.add_widget(self.title_input)
        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel = styled_button("Cancel", theme)
        cancel.bind(on_release=lambda *_: self.dismiss())
        create = styled_button("Create", theme, primary=True)
        create.bind(on_release=self._create)
        actions.add_widget(cancel)
        actions.add_widget(create)
        card.add_widget(actions)
        self.add_widget(card)

    def on_open(self) -> None:
        self.title_input.focus = True

    def _create(self, *_args) -> None:
        title = self.title_input.text.strip()
        if title:
            self.on_create(title)
            self.dismiss()
        else:
            self.title_input.focus = True


class ConfirmDialog(ModalView):
    """Ask before a destructive operation."""

    def __init__(
        self,
        theme: Theme,
        message: str,
        on_confirm: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(
            size_hint=(0.9, None),
            height=dp(210),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        card = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
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
        card.add_widget(
            Label(
                text=message,
                color=theme.color("text"),
                font_size=sp(16),
                halign="left",
                valign="middle",
                text_size=(dp(300), None),
            )
        )
        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel = styled_button("Cancel", theme)
        cancel.bind(on_release=lambda *_: self.dismiss())
        confirm = styled_button("Delete", theme)
        confirm.background_color = theme.color("destructive")
        confirm.color = theme.color("on_accent")
        confirm.bind(on_release=lambda *_: (on_confirm(), self.dismiss()))
        actions.add_widget(cancel)
        actions.add_widget(confirm)
        card.add_widget(actions)
        self.add_widget(card)
