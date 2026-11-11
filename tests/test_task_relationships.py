import pytest

from minitask.core.exceptions import TaskHierarchyError
from minitask.core.task_service import TaskService


def test_subtasks_inherit_long_term_membership(database):
    tasks = TaskService(database)
    parent = tasks.create_task("Finish compiler")
    child = tasks.create_subtask(parent.id, "Implement lexer")
    daily_parent = tasks.create_task("Buy groceries", is_long_term=False)
    daily_child = tasks.create_subtask(daily_parent.id, "Buy milk")

    assert parent.is_long_term is True
    assert child.is_long_term is True
    assert child.parent_id == parent.id
    assert daily_child.is_long_term is False
    assert daily_child.parent_id == daily_parent.id
    with pytest.raises(TaskHierarchyError, match="same collection"):
        tasks.create_task("Misplaced child", parent_id=parent.id, is_long_term=False)


def test_prevents_self_parent_and_descendant_cycles(database):
    tasks = TaskService(database)
    parent = tasks.create_task("Project")
    child = tasks.create_subtask(parent.id, "Phase")
    grandchild = tasks.create_subtask(child.id, "Step")

    with pytest.raises(TaskHierarchyError, match="own parent"):
        tasks.update_task(parent.id, parent_id=parent.id)
    with pytest.raises(TaskHierarchyError, match="descendant"):
        tasks.update_task(parent.id, parent_id=grandchild.id)
    with pytest.raises(TaskHierarchyError, match="descendant"):
        tasks.update_task(child.id, parent_id=grandchild.id)

    assert tasks.get_task(parent.id).parent_id is None
    assert tasks.get_task(child.id).parent_id == parent.id


def test_reparenting_preserves_identity_and_tree_order(database):
    tasks = TaskService(database)
    first_parent = tasks.create_task("First project")
    second_parent = tasks.create_task("Second project")
    child = tasks.create_subtask(first_parent.id, "Subtask")

    moved = tasks.update_task(child.id, parent_id=second_parent.id)

    assert moved.id == child.id
    assert moved.parent_id == second_parent.id
    assert [task.title for task in tasks.list_all()] == [
        "First project",
        "Second project",
        "Subtask",
    ]
    tree = tasks.tree()
    assert tree[0].children == ()
    assert [node.task.title for node in tree[1].children] == ["Subtask"]


def test_long_term_listing_excludes_daily_only_task_tree(database):
    tasks = TaskService(database)
    long_term = tasks.create_task("Long-term")
    tasks.create_subtask(long_term.id, "Long-term subtask")
    daily = tasks.create_task("Today only", is_long_term=False)
    tasks.create_subtask(daily.id, "Daily subtask")

    assert [task.title for task in tasks.list_long_term()] == [
        "Long-term",
        "Long-term subtask",
    ]
