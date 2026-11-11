"""Long-term task hierarchy screen."""

from minitask.ui.screens.task_tree import TaskTreeScreen


class LongTermScreen(TaskTreeScreen):
    def __init__(self, tasks, theme, shell, **kwargs) -> None:
        super().__init__(
            "long_term",
            "Long-term",
            tasks,
            theme,
            shell,
            long_term_only=True,
            **kwargs,
        )
