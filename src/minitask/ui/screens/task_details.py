"""Task details editor and linked daily assignment actions."""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from minitask.core.exceptions import MiniTaskError
from minitask.core.daily_plan_service import DailyPlanService
from minitask.core.task_service import TaskService
from minitask.database import Database
from minitask.ui.theme import Theme
from minitask.ui.widgets.date_picker import CalendarPicker
from minitask.ui.widgets.task_dialogs import ConfirmDialog, styled_button
from minitask.ui.widgets.text import align_label


class TaskDetailsScreen(Screen):
    """View and edit a task without creating a second task record."""

    def __init__(
        self,
        database: Database,
        tasks: TaskService,
        plans: DailyPlanService,
        theme: Theme,
        shell,
        **kwargs,
    ) -> None:
        super().__init__(name="task_details", **kwargs)
        self.database = database
        self.tasks = tasks
        self.plans = plans
        self.theme = theme
        self.shell = shell
        self.task_id: int | None = None
        self._draw_background()

        page = BoxLayout(
            orientation="vertical",
            padding=dp(theme.page_padding),
            spacing=dp(8),
        )
        header = BoxLayout(
            size_hint_y=None, height=dp(theme.touch_target), spacing=dp(theme.spacing)
        )
        back = Button(
            text="‹",
            size_hint_x=None,
            width=dp(44),
            background_normal="",
            background_color=theme.color("elevated"),
            color=theme.color("accent"),
            font_size=sp(26),
        )
        back.bind(on_release=lambda *_: self.shell.go_back())
        header.add_widget(back)
        header.add_widget(
            align_label(Label(
                text="Task details",
                color=theme.color("text"),
                font_size=sp(22),
                bold=True,
                halign="left",
            ))
        )
        page.add_widget(header)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        form = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(8)
        )
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(self._field_label("Title"))
        self.title_input = self._text_input(multiline=False, height=48)
        self.title_input.hint_text = "Task title"
        form.add_widget(self.title_input)

        form.add_widget(self._field_label("Parent"))
        self.parent_label = align_label(Label(
            text="No parent",
            size_hint_y=None,
            height=dp(42),
            color=theme.color("secondary"),
            font_size=sp(15),
            halign="left",
            valign="middle",
        ))
        form.add_widget(self.parent_label)

        form.add_widget(self._field_label("Deadline"))
        deadline_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.deadline_input = self._text_input(multiline=False, height=48)
        self.deadline_input.readonly = True
        self.deadline_input.hint_text = "No deadline"
        deadline_row.add_widget(self.deadline_input)
        choose_date = styled_button("Choose date", theme)
        choose_date.size_hint_x = None
        choose_date.width = dp(112)
        choose_date.bind(on_release=lambda *_: self._open_date_picker())
        deadline_row.add_widget(choose_date)
        form.add_widget(deadline_row)

        form.add_widget(self._field_label("Notes"))
        self.notes_input = self._text_input(multiline=True, height=150)
        self.notes_input.hint_text = "Add notes"
        self.notes_input.valign = "top"
        form.add_widget(self.notes_input)

        completion_row = BoxLayout(
            size_hint_y=None, height=dp(48), spacing=dp(10)
        )
        self.completion = CheckBox(
            size_hint_x=None,
            width=dp(44),
            color=theme.color("accent"),
        )
        completion_row.add_widget(self.completion)
        completion_row.add_widget(
            align_label(Label(
                text="Completed",
                color=theme.color("text"),
                font_size=sp(15),
                halign="left",
            ))
        )
        form.add_widget(completion_row)
        scroll.add_widget(form)
        page.add_widget(scroll)

        self.status = align_label(Label(
            text="",
            size_hint_y=None,
            height=dp(24),
            color=theme.color("secondary"),
            font_size=sp(12),
            halign="left",
        ))
        page.add_widget(self.status)

        plan_actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        add_today = styled_button("Add to Today", theme)
        add_today.bind(on_release=lambda *_: self._add_to_today())
        add_tomorrow = styled_button("Add to Tomorrow", theme)
        add_tomorrow.bind(on_release=lambda *_: self._add_to_tomorrow())
        plan_actions.add_widget(add_today)
        plan_actions.add_widget(add_tomorrow)
        page.add_widget(plan_actions)

        edit_actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        save = styled_button("Save", theme, primary=True)
        save.bind(on_release=lambda *_: self.save())
        delete = styled_button("Delete task", theme)
        delete.background_color = theme.color("destructive")
        delete.color = theme.color("on_accent")
        delete.bind(on_release=lambda *_: self._confirm_delete())
        edit_actions.add_widget(delete)
        edit_actions.add_widget(save)
        page.add_widget(edit_actions)
        self.add_widget(page)

    def _draw_background(self) -> None:
        with self.canvas.before:
            Color(*self.theme.color("window"))
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda _widget, value: setattr(self._background, "pos", value),
            size=lambda _widget, value: setattr(self._background, "size", value),
        )

    def _field_label(self, text: str) -> Label:
        return align_label(Label(
            text=text,
            size_hint_y=None,
            height=dp(26),
            color=self.theme.color("secondary"),
            font_size=sp(13),
            halign="left",
        ))

    def _text_input(self, *, multiline: bool, height: int) -> TextInput:
        return TextInput(
            multiline=multiline,
            size_hint_y=None,
            height=dp(self.theme.field_height if height == 48 else height),
            padding=(dp(12), dp(10)),
            background_normal="",
            background_active="",
            background_color=self.theme.color("card"),
            foreground_color=self.theme.color("text"),
            cursor_color=self.theme.color("accent"),
            hint_text_color=self.theme.color("secondary"),
            font_size=sp(16),
        )

    def set_task(self, task_id: int) -> None:
        self.task_id = task_id
        self.load()

    def load(self) -> None:
        if self.task_id is None:
            return
        task = self.tasks.get_task(self.task_id)
        self.title_input.text = task.title
        self.notes_input.text = task.notes or ""
        self.deadline_input.text = task.due_date or ""
        self.completion.active = task.is_completed
        if task.parent_id is None:
            self.parent_label.text = "No parent"
        else:
            self.parent_label.text = self.tasks.get_task(task.parent_id).title
        self.status.text = ""

    def save(self) -> None:
        if self.task_id is None:
            return
        try:
            with self.database.transaction():
                self.tasks.update_task(
                    self.task_id,
                    title=self.title_input.text,
                    notes=self.notes_input.text or None,
                    due_date=self.deadline_input.text or None,
                )
                self.tasks.set_completed(self.task_id, self.completion.active)
            self.shell.refresh_task_views()
            self.shell.go_back()
        except Exception as exc:
            self.show_error(exc)

    def _open_date_picker(self) -> None:
        picker = CalendarPicker(
            self.theme,
            self._set_deadline,
            self.deadline_input.text or None,
        )
        picker.open()

    def _set_deadline(self, value: str | None) -> None:
        self.deadline_input.text = value or ""

    def _add_to_today(self) -> None:
        if self.task_id is None:
            return
        try:
            self.plans.add_existing_task(self.task_id, self.plans.today_date())
            self.shell.refresh_task_views()
            self.status.color = self.theme.color("success")
            self.status.text = "Added to Today."
        except Exception as exc:
            self.show_error(exc)

    def _add_to_tomorrow(self) -> None:
        if self.task_id is None:
            return
        try:
            self.plans.add_existing_task(self.task_id, self.plans.tomorrow_date())
            self.shell.refresh_task_views()
            self.status.color = self.theme.color("success")
            self.status.text = "Added to Tomorrow."
        except Exception as exc:
            self.show_error(exc)

    def _confirm_delete(self) -> None:
        if self.task_id is None:
            return
        task = self.tasks.get_task(self.task_id)
        dialog = ConfirmDialog(
            self.theme,
            f"Delete ‘{task.title}’, its subtasks, and daily assignments?",
            self._delete,
        )
        dialog.open()

    def _delete(self) -> None:
        if self.task_id is None:
            return
        try:
            self.tasks.delete_task(self.task_id)
            self.shell.refresh_task_views()
            self.shell.go_back()
        except Exception as exc:
            self.show_error(exc)

    def show_error(self, error: Exception) -> None:
        self.status.color = self.theme.color("destructive")
        self.status.text = (
            str(error) if isinstance(error, MiniTaskError) else "Could not save task."
        )
