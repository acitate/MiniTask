"""Initial SQLite schema for MiniTask."""

SCHEMA_VERSION = 1

INITIAL_SCHEMA = """
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    notes TEXT NULL,
    is_long_term INTEGER NOT NULL DEFAULT 1 CHECK (is_long_term IN (0, 1)),
    due_date TEXT NULL CHECK (
        due_date IS NULL OR (
            length(due_date) = 10
            AND due_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        )
    ),
    is_completed INTEGER NOT NULL DEFAULT 0 CHECK (is_completed IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (parent_id IS NULL OR parent_id != id)
);

CREATE INDEX tasks_parent_id_idx ON tasks(parent_id);
CREATE INDEX tasks_long_term_idx ON tasks(is_long_term);

CREATE TABLE daily_plan_items (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    plan_date TEXT NOT NULL CHECK (
        length(plan_date) = 10
        AND plan_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    ),
    position INTEGER NOT NULL CHECK (position >= 0),
    UNIQUE (task_id, plan_date)
);

CREATE INDEX daily_plan_date_position_idx
    ON daily_plan_items(plan_date, position, id);
"""
