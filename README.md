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

The initial scaffold is intentionally small. The database, task-management
core, Kivy interface, and Android packaging are being added incrementally.
