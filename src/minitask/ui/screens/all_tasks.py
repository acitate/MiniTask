"""Global task hierarchy screen."""

from minitask.ui.screens.task_tree import TaskTreeScreen


class AllTasksScreen(TaskTreeScreen):
    def __init__(self, tasks, theme, shell, **kwargs) -> None:
        super().__init__(
            "all_tasks",
            "All",
            tasks,
            theme,
            shell,
            long_term_only=False,
            **kwargs,
        )
