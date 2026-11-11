"""SQLite connection lifecycle and transaction helpers."""

import sqlite3
from contextlib import contextmanager
from itertools import count
from pathlib import Path
from typing import Iterator

from minitask.core.exceptions import DatabaseError
from minitask.database.migrations import migrate


def utc_timestamp() -> str:
    """Return a sortable UTC timestamp in ISO 8601 format."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


class Database:
    """Own a configured SQLite connection and initialize its schema."""

    def __init__(self, path: str | Path) -> None:
        self.path = (
            str(Path(path).expanduser()) if str(path) != ":memory:" else ":memory:"
        )
        self._savepoint_ids = count(1)
        try:
            if self.path != ":memory:":
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self._connection: sqlite3.Connection | None = sqlite3.connect(
                self.path, isolation_level=None
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA busy_timeout = 5000")
            migrate(self._connection)
        except (OSError, sqlite3.Error, DatabaseError) as exc:
            if hasattr(self, "_connection"):
                self._connection.close()
            if isinstance(exc, DatabaseError):
                raise
            raise DatabaseError(f"Could not open database at {self.path!r}.") from exc

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the configured connection used by repositories."""
        if self._connection is None:
            raise DatabaseError("The database connection is closed.")
        return self._connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a group of statements atomically, rolling back on failure."""
        connection = self.connection
        nested = connection.in_transaction
        savepoint = f"minitask_sp_{next(self._savepoint_ids)}"
        try:
            statement = f"SAVEPOINT {savepoint}" if nested else "BEGIN IMMEDIATE"
            connection.execute(statement)
            yield connection
            if nested:
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            else:
                connection.commit()
        except Exception:
            if connection.in_transaction:
                if nested:
                    connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                else:
                    connection.rollback()
            raise

    def close(self) -> None:
        """Close this database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
