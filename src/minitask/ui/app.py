"""Kivy application startup and private database location."""

import os
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform

from minitask.database import Database
from minitask.ui.navigation import NavigationShell
from minitask.ui.theme import Theme


class MiniTaskApp(App):
    """Offline-first MiniTask user interface."""

    title = "MiniTask"

    def build(self) -> NavigationShell:
        self.theme = Theme()
        Window.clearcolor = self.theme.color("window")
        if platform == "android":
            data_directory = Path(self.user_data_dir)
        else:
            config_directory = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            )
            data_directory = config_directory / "minitask"
            data_directory.mkdir(parents=True, exist_ok=True)
        database_path = data_directory / "minitask.sqlite3"
        self.database = Database(database_path)
        return NavigationShell(self.database, self.theme)

    def on_stop(self) -> None:
        database = getattr(self, "database", None)
        if database is not None:
            database.close()

    def on_resume(self) -> bool:
        shell = getattr(self, "root", None)
        if shell is not None:
            shell.on_app_resume()
        return True
