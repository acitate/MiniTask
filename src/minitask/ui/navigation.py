"""Four-destination bottom navigation and detail-screen routing."""

from kivy.graphics import Color, InstructionGroup, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import NoTransition, ScreenManager
from kivy.core.window import Window

from minitask.core.daily_plan_service import DailyPlanService
from minitask.core.task_service import TaskService
from minitask.database import Database
from minitask.ui.screens.all_tasks import AllTasksScreen
from minitask.ui.screens.long_term import LongTermScreen
from minitask.ui.screens.task_details import TaskDetailsScreen
from minitask.ui.screens.today import TodayScreen
from minitask.ui.screens.tomorrow import TomorrowScreen
from minitask.ui.theme import Theme


class NavigationShell(BoxLayout):
    """Own app services, the four primary views, and secondary details view."""

    tabs = (
        ("today", "Today"),
        ("tomorrow", "Tomorrow"),
        ("long_term", "Long-term"),
        ("all_tasks", "All"),
    )

    def __init__(self, database: Database, theme: Theme, **kwargs) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self.database = database
        self.theme = theme
        self.task_service = TaskService(database)
        self.plan_service = DailyPlanService(
            database, task_service=self.task_service
        )
        self.current_tab = "today"
        self.return_tab = "today"
        self._tab_buttons: dict[str, Button] = {}

        self.manager = ScreenManager(transition=NoTransition())
        self.today_screen = TodayScreen(
            self.task_service, self.plan_service, theme, self
        )
        self.tomorrow_screen = TomorrowScreen(
            self.task_service, self.plan_service, theme, self
        )
        self.long_term_screen = LongTermScreen(self.task_service, theme, self)
        self.all_screen = AllTasksScreen(self.task_service, theme, self)
        self.details_screen = TaskDetailsScreen(
            database, self.task_service, self.plan_service, theme, self
        )
        for screen in (
            self.today_screen,
            self.tomorrow_screen,
            self.long_term_screen,
            self.all_screen,
            self.details_screen,
        ):
            self.manager.add_widget(screen)
        self.manager.current = "today"
        self.add_widget(self.manager)

        self.nav_bar = BoxLayout(
            size_hint_y=None,
            height=dp(theme.navigation_height),
            spacing=dp(2),
            padding=(dp(4), dp(4)),
        )
        with self.nav_bar.canvas.before:
            Color(*theme.color("card"))
            self._nav_background = Rectangle(
                pos=self.nav_bar.pos, size=self.nav_bar.size
            )
            Color(*theme.color("border"))
            self._nav_border = Rectangle(
                pos=(self.nav_bar.x, self.nav_bar.top - dp(0.7)),
                size=(self.nav_bar.width, dp(0.7)),
            )
        self.nav_bar.bind(pos=self._update_nav_canvas, size=self._update_nav_canvas)
        for name, label in self.tabs:
            button = NavigationTab(
                text=label,
                icon=name,
                theme=theme,
                selected=name == "today",
            )
            button.bind(on_release=lambda _button, tab=name: self.select_tab(tab))
            self._tab_buttons[name] = button
            self.nav_bar.add_widget(button)
        self.add_widget(self.nav_bar)
        Window.bind(on_keyboard=self._on_keyboard)

    def _update_nav_canvas(self, *_args) -> None:
        self._nav_background.pos = self.nav_bar.pos
        self._nav_background.size = self.nav_bar.size
        self._nav_border.pos = (self.nav_bar.x, self.nav_bar.top - dp(0.7))
        self._nav_border.size = (self.nav_bar.width, dp(0.7))

    def select_tab(self, name: str) -> None:
        self.current_tab = name
        self.return_tab = name
        self.manager.current = name
        self.nav_bar.height = dp(self.theme.navigation_height)
        self.nav_bar.opacity = 1
        self.nav_bar.disabled = False
        for tab, _label in self.tabs:
            self._tab_buttons[tab].set_selected(tab == name)

    def open_details(self, task_id: int) -> None:
        self.return_tab = self.current_tab
        self.details_screen.set_task(task_id)
        self.manager.current = "task_details"
        self.nav_bar.height = 0
        self.nav_bar.opacity = 0
        self.nav_bar.disabled = True

    def go_back(self) -> None:
        self.refresh_task_views()
        self.select_tab(self.return_tab)

    def refresh_task_views(self) -> None:
        for screen in (
            self.today_screen,
            self.tomorrow_screen,
            self.long_term_screen,
            self.all_screen,
        ):
            screen.refresh()

    def _on_keyboard(self, _window, key, *_args) -> bool:
        if key == 27 and self.manager.current == "task_details":
            self.go_back()
            return True
        return False


class NavigationTab(Button):
    """Bottom tab button with a small line icon drawn by Kivy canvas."""

    def __init__(
        self, *, icon: str, theme: Theme, selected: bool, **kwargs
    ) -> None:
        super().__init__(
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=theme.color("accent" if selected else "secondary"),
            font_size=sp(12),
            halign="center",
            valign="bottom",
            padding=(0, dp(6)),
            **kwargs,
        )
        self.icon = icon
        self.theme = theme
        self.text_size = self.size
        self._group = InstructionGroup()
        self._icon_color = Color(*self.color)
        self._group.add(self._icon_color)
        self.canvas.after.add(self._group)
        self.bind(size=self._update_icon, pos=self._update_icon)
        self._update_icon()

    def set_selected(self, selected: bool) -> None:
        self.color = self.theme.color("accent" if selected else "secondary")
        self._icon_color.rgba = self.color

    def _update_icon(self, *_args) -> None:
        self.text_size = self.size
        self._group.clear()
        self._group.add(self._icon_color)
        center_x = self.center_x
        center_y = self.y + self.height * 0.68
        width = dp(1.5)
        if self.icon == "today":
            self._group.add(Line(circle=(center_x, center_y, dp(7)), width=width))
            self._group.add(
                Line(
                    points=[center_x - dp(3), center_y, center_x + dp(3), center_y],
                    width=width,
                )
            )
        elif self.icon == "tomorrow":
            self._group.add(Line(circle=(center_x, center_y, dp(7)), width=width))
            self._group.add(
                Line(
                    points=[center_x, center_y, center_x, center_y + dp(4)],
                    width=width,
                )
            )
            self._group.add(
                Line(
                    points=[center_x, center_y, center_x + dp(4), center_y],
                    width=width,
                )
            )
        elif self.icon == "long_term":
            for offset in (dp(6), 0, -dp(6)):
                self._group.add(
                    Line(
                        rectangle=(center_x - dp(10), center_y + offset, dp(4), dp(4)),
                        width=width,
                    )
                )
                self._group.add(
                    Line(
                        points=[
                            center_x - dp(2),
                            center_y + offset + dp(2),
                            center_x + dp(10),
                            center_y + offset + dp(2),
                        ],
                        width=width,
                    )
                )
        else:
            for offset in (dp(5), 0, -dp(5)):
                self._group.add(
                    Line(
                        points=[
                            center_x - dp(9),
                            center_y + offset,
                            center_x + dp(9),
                            center_y + offset,
                        ],
                        width=width,
                    )
                )
