"""Kivy-independent task rules and hierarchy queries."""

from minitask.core.exceptions import TaskHierarchyError
from minitask.core.models import Task, TaskTreeNode
from minitask.database import Database, TaskRepository

_UNSET = object()


class TaskService:
    """Apply task-management rules using the SQLite task repository."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.repository = TaskRepository(database)

    def create_task(
        self,
        title: str,
        *,
        parent_id: int | None = None,
        notes: str | None = None,
        due_date: str | None = None,
        is_long_term: bool | None = None,
    ) -> Task:
        """Create a task, inheriting collection membership from its parent."""
        with self.database.transaction():
            if parent_id is not None:
                parent = self.repository.get(parent_id)
                if is_long_term is not None and is_long_term != parent.is_long_term:
                    raise TaskHierarchyError(
                        "A subtask must use the same collection as its parent."
                    )
                is_long_term = parent.is_long_term
            elif is_long_term is None:
                is_long_term = True

            return self.repository.create(
                title,
                parent_id=parent_id,
                notes=notes,
                due_date=due_date,
                is_long_term=is_long_term,
            )

    def create_subtask(
        self,
        parent_id: int,
        title: str,
        *,
        notes: str | None = None,
        due_date: str | None = None,
    ) -> Task:
        """Create a child task that remains part of its parent's collection."""
        return self.create_task(
            title,
            parent_id=parent_id,
            notes=notes,
            due_date=due_date,
        )

    def get_task(self, task_id: int) -> Task:
        return self.repository.get(task_id)

    def update_task(
        self,
        task_id: int,
        *,
        title: str | object = _UNSET,
        notes: str | None | object = _UNSET,
        due_date: str | None | object = _UNSET,
        parent_id: int | None | object = _UNSET,
    ) -> Task:
        """Edit task fields while preserving an acyclic, coherent hierarchy."""
        with self.database.transaction():
            task = self.repository.get(task_id)
            if parent_id is not _UNSET:
                if parent_id == task_id:
                    raise TaskHierarchyError("A task cannot be its own parent.")
                if parent_id is not None:
                    parent = self.repository.get(parent_id)
                    if parent.is_long_term != task.is_long_term:
                        raise TaskHierarchyError(
                            "A task and its parent must belong to the same collection."
                        )
                    self._ensure_not_descendant(task_id, parent_id)
            changes = {}
            for name, value in (
                ("title", title),
                ("notes", notes),
                ("due_date", due_date),
                ("parent_id", parent_id),
            ):
                if value is not _UNSET:
                    changes[name] = value
            return self.repository.update(task_id, **changes)

    def set_completed(self, task_id: int, completed: bool) -> Task:
        """Set completion on this task only; subtasks remain independent."""
        return self.repository.update(task_id, is_completed=completed)

    def delete_task(self, task_id: int) -> None:
        """Delete a task and its descendants and daily assignments."""
        self.repository.delete(task_id)

    def list_all(self) -> list[Task]:
        """Return every task in parent-before-child order."""
        return self._flatten(self.tree())

    def list_long_term(self) -> list[Task]:
        """Return long-term tasks in parent-before-child order."""
        return self._flatten(self.tree(long_term_only=True))

    def tree(self, *, long_term_only: bool = False) -> list[TaskTreeNode]:
        """Build a task hierarchy for All or Long-term presentation."""
        tasks = (
            self.repository.list_long_term()
            if long_term_only
            else self.repository.list_all()
        )
        task_by_id = {task.id: task for task in tasks}
        children: dict[int, list[Task]] = {}
        for task in tasks:
            if task.parent_id in task_by_id:
                children.setdefault(task.parent_id, []).append(task)

        visited: set[int] = set()

        def build(task: Task) -> TaskTreeNode:
            visited.add(task.id)
            child_nodes = tuple(
                build(child)
                for child in children.get(task.id, [])
                if child.id not in visited
            )
            return TaskTreeNode(task=task, children=child_nodes)

        roots = [task for task in tasks if task.parent_id not in task_by_id]
        nodes = [build(root) for root in roots]
        # Keep even malformed legacy cycles visible instead of losing their tasks.
        nodes.extend(build(task) for task in tasks if task.id not in visited)
        return nodes

    def _ensure_not_descendant(self, task_id: int, proposed_parent_id: int) -> None:
        """Reject reparenting beneath the task or any of its descendants."""
        pending = [task_id]
        descendants: set[int] = set()
        while pending:
            current_id = pending.pop()
            if current_id in descendants:
                continue
            descendants.add(current_id)
            pending.extend(
                child.id for child in self.repository.list_children(current_id)
            )
        if proposed_parent_id in descendants:
            raise TaskHierarchyError("A task cannot be moved under its descendant.")

    @staticmethod
    def _flatten(nodes: list[TaskTreeNode]) -> list[Task]:
        flattened: list[Task] = []

        def visit(node: TaskTreeNode) -> None:
            flattened.append(node.task)
            for child in node.children:
                visit(child)

        for node in nodes:
            visit(node)
        return flattened
