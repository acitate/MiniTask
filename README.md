# MiniTask

MiniTask is an offline-first task planner for Android, built with Python and
Kivy. Tasks are stored locally in SQLite, while daily plans contain references
to those tasks so that completion and edits stay consistent across views.

## Development

Install [UV](https://docs.astral.sh/uv/), then sync the project environment:

```sh
uv sync
```

Run the current application entry point with:

```sh
uv run minitask
# or: uv run python -m minitask.main
```

Run the test suite with:

```sh
uv run pytest
```

## Database layer

The SQLite database is initialized and migrated when `minitask.database.Database`
is opened. It enables foreign keys and stores schema version 1 in
`PRAGMA user_version`. Task data is accessed through `TaskRepository`; daily
assignments are references managed by `DailyPlanRepository`. The repositories
accept a `Database` instance, and multi-step work can use its transaction
context manager. Timestamps are UTC ISO 8601 strings and dates use `YYYY-MM-DD`.

## Interface

The Kivy app opens on Today and provides Today, Tomorrow, Long-term, and All
through bottom navigation. Daily rows support completion, manual ordering, and
removing an assignment without deleting its task. Long-term and All show
expandable task trees. Task details include notes, a calendar deadline picker,
linked assignment actions, and delete confirmation. Android stores SQLite in
Kivy's private app data directory. Light and dark Adwaita-inspired palettes are
available; Android follows the system appearance, while desktop can use
`MINITASK_THEME=light` or `MINITASK_THEME=dark`.

Android packaging and final UX/reliability refinement remain future phases.

## Core services

`TaskService` owns task validation, hierarchy, edits, independent completion,
and All/Long-term hierarchy queries. `DailyPlanService` stores manual date
assignments, exposes Today and Tomorrow from the current local date, and can
create and assign a daily task atomically. Deadlines do not create assignments,
and removing an assignment leaves its task intact. Both services can be used
without importing Kivy.
