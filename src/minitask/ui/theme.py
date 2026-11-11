"""Central Adwaita-inspired colors and dimensions for the Kivy interface."""

import os

from kivy.utils import platform


def _rgba(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)) + (
        1.0,
    )


LIGHT = {
    "window": _rgba("#FAFAFA"),
    "card": _rgba("#FFFFFF"),
    "elevated": _rgba("#F0F0F0"),
    "text": _rgba("#241F31"),
    "secondary": _rgba("#77767B"),
    "accent": _rgba("#3584E4"),
    "destructive": _rgba("#E01B24"),
    "success": _rgba("#26A269"),
    "border": _rgba("#E2E2E2"),
    "on_accent": _rgba("#FFFFFF"),
    "disabled": _rgba("#B8B8B8"),
}

DARK = {
    "window": _rgba("#242424"),
    "card": _rgba("#303030"),
    "elevated": _rgba("#383838"),
    "text": _rgba("#FFFFFF"),
    "secondary": _rgba("#A0A0A0"),
    "accent": _rgba("#78AEED"),
    "destructive": _rgba("#FF7B63"),
    "success": _rgba("#57E389"),
    "border": _rgba("#484848"),
    "on_accent": _rgba("#242424"),
    "disabled": _rgba("#6D6D6D"),
}


class Theme:
    """Resolve light or dark colors, following Android appearance when available."""

    spacing = 8
    page_padding = 16
    section_spacing = 12
    row_height = 58
    corner_radius = 12
    touch_target = 48
    compact_action = 40
    navigation_height = 70
    field_height = 48

    def __init__(self, dark: bool | None = None) -> None:
        self.dark = self._system_dark() if dark is None else dark
        self.colors = DARK if self.dark else LIGHT

    @staticmethod
    def _system_dark() -> bool:
        override = os.environ.get("MINITASK_THEME", "").lower()
        if override in {"dark", "light"}:
            return override == "dark"
        if platform == "android":
            try:
                from jnius import autoclass

                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                ui_mode = activity.getResources().getConfiguration().uiMode
                return (ui_mode & 0x30) == 0x20
            except Exception:
                pass
        return False

    def color(self, name: str) -> tuple[float, float, float, float]:
        return self.colors[name]
