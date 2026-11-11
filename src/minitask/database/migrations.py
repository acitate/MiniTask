"""Explicit database schema migrations."""

import sqlite3

from minitask.core.exceptions import DatabaseError
from minitask.database.schema import INITIAL_SCHEMA, SCHEMA_VERSION


def migrate(connection: sqlite3.Connection) -> None:
    """Bring a connection's schema up to the current version."""
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version > SCHEMA_VERSION:
        raise DatabaseError(
            f"Database schema version {version} is newer than supported "
            f"version {SCHEMA_VERSION}."
        )

    try:
        if version == 0:
            connection.execute("BEGIN IMMEDIATE")
            for statement in INITIAL_SCHEMA.split(";"):
                if statement.strip():
                    connection.execute(statement)
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            connection.commit()
    except sqlite3.Error as exc:
        if connection.in_transaction:
            connection.rollback()
        raise DatabaseError("Could not migrate the MiniTask database.") from exc
