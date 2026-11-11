"""Exceptions shared by the task core and persistence layer."""


class MiniTaskError(Exception):
    """Base class for expected MiniTask errors."""


class TaskNotFoundError(MiniTaskError):
    """Raised when an operation refers to a missing task."""


class DailyAssignmentNotFoundError(MiniTaskError):
    """Raised when a daily assignment does not exist."""


class DuplicateDailyAssignmentError(MiniTaskError):
    """Raised when a task is already assigned to the selected date."""


class InvalidTaskError(MiniTaskError):
    """Raised when task data does not satisfy the persistence contract."""


class DatabaseError(MiniTaskError):
    """Raised when the database cannot be initialized or queried safely."""
