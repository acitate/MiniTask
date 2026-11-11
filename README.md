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

Today and Tomorrow refresh after a local date change, including after the app
returns from the background. Unexpected UI and storage errors are logged for
diagnosis and shown as concise recovery messages. Transaction and persistence
tests cover rollback after interrupted work and reopening the local database.
Android debug build instructions follow.

## Android debug build

Android builds use Buildozer and python-for-android. On Ubuntu, install the
system build tools listed in the [Buildozer Android installation guide](https://buildozer.readthedocs.io/en/latest/installation/),
including OpenJDK 17, then create a separate Buildozer environment:

```sh
uv venv --python 3.14 .buildozer-venv
.buildozer-venv/bin/python -m ensurepip
uv pip install --python .buildozer-venv/bin/python \
  git+https://github.com/kivy/buildozer legacy-cgi setuptools cython==0.29.34
. .buildozer-venv/bin/activate
buildozer android debug
```

The first build downloads the Android SDK and NDK. Buildozer places the debug
APK in `bin/`. To install it on a connected Android device with USB debugging
enabled, run `adb install -r bin/<debug-apk-name>.apk`. The app requests no
Android permissions, stores its SQLite database under Kivy's private
`user_data_dir`, and disables Android automatic backup. It does not require
network access.

The spec targets Android API 36 with a minimum API of 24 and builds ARM64 and
32-bit ARM APKs. It pins the Android Python runtime to 3.14.2 and Kivy to 2.3.2.
`p4a.branch = develop` is required for python-for-android's Python 3.14 support.
See the [Buildozer specification reference](https://buildozer.readthedocs.io/en/latest/specifications/)
and [python-for-android build options](https://github.com/kivy/python-for-android/blob/develop/doc/source/buildoptions.rst)
for the current toolchain settings.

## Core services

`TaskService` owns task validation, hierarchy, edits, independent completion,
and All/Long-term hierarchy queries. `DailyPlanService` stores manual date
assignments, exposes Today and Tomorrow from the current local date, and can
create and assign a daily task atomically. Deadlines do not create assignments,
and removing an assignment leaves its task intact. Both services can be used
without importing Kivy.
