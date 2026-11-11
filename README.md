# MiniTask

MiniTask is a small, offline-first task planner for Android, built with Python
and Kivy. It has four views: Today, Tomorrow, Long-term, and All. A task is
stored once; daily plans hold dated references to tasks, so completion and
edits stay in sync everywhere.

## Install and run on desktop

Requirements: Python 3.14 or newer and [UV](https://docs.astral.sh/uv/).
From the repository root:

```sh
uv sync --locked
uv run minitask
```

Alternatively, start the module directly with `uv run python -m minitask.main`.
The desktop database lives in the platform's user data directory. Set
`MINITASK_THEME=light` or `MINITASK_THEME=dark` to choose a desktop theme.

## Development

```sh
uv sync --locked
uv run pytest
```

The checked-in `uv.lock` pins the development and desktop dependency graph.
Runtime dependencies are Kivy (`>=2.3.2,<3`); tests use pytest (`>=8.3,<9`).
SQLite and all other core persistence features use Python's standard library.
Buildozer, its Android build tools, and the Android SDK/NDK are only needed for
Android packaging and are kept outside the UV project environment.

## Architecture

The code is under `src/minitask` and follows three layers:

- `core/` defines immutable task models and task/daily-plan services. It
  validates business rules and stays independent of Kivy; services use the
  database repositories for persistence.
- `database/` owns SQLite connections, migrations, transactions, and
  repositories. Repositories map database rows to core models.
- `ui/` contains the Kivy app, navigation, screens, reusable widgets, and
  Adwaita-inspired theme. UI code calls core services instead of executing SQL.
- `main.py` and the package entry point start the application.

Task completion is stored on the task. A daily assignment only links the task
to a plan date; deleting an assignment does not delete the task. Deadlines are
metadata and never create daily assignments. Today and Tomorrow resolve their
dates from the device's local calendar and do not roll unfinished items over.

## SQLite schema

`Database` creates the database directory, enables foreign keys, and runs
migrations on open. The current schema version is **1**, stored in
`PRAGMA user_version`. Migrations are implemented in
`src/minitask/database/migrations.py`; the version 1 DDL is in
`src/minitask/database/schema.py`.

### `tasks`

| Column | Meaning |
| --- | --- |
| `id` | Unique task ID (`INTEGER PRIMARY KEY`) |
| `parent_id` | Optional parent task; deleting a parent cascades to descendants |
| `title` | Required, trimmed, non-empty task title |
| `notes` | Optional plain text |
| `is_long_term` | Boolean integer indicating membership in Long-term |
| `due_date` | Optional ISO calendar date (`YYYY-MM-DD`) |
| `is_completed` | Independent completion state for this task |
| `created_at` | UTC ISO 8601 timestamp |
| `updated_at` | UTC ISO 8601 timestamp, refreshed on edits |

### `daily_plan_items`

| Column | Meaning |
| --- | --- |
| `id` | Unique assignment row ID |
| `task_id` | Reference to `tasks.id`, deleted when its task is deleted |
| `plan_date` | Calendar date in `YYYY-MM-DD` form |
| `position` | Non-negative manual ordering position within the date |

The unique constraint on (`task_id`, `plan_date`) prevents duplicate daily
assignments, while allowing a task on multiple dates. Date/position indexes
support ordered plan reads; parent and long-term indexes support task listing.
Repositories use parameterized SQL. Multi-step operations use transactions,
with rollback on failure.

## Android debug APK

Android packaging uses Buildozer and python-for-android; UV remains the
development dependency manager. On Ubuntu, install the system packages from
the [Buildozer Android installation guide](https://buildozer.readthedocs.io/en/latest/installation/),
including OpenJDK 17, then create the isolated Buildozer environment:

```sh
uv venv --python 3.14 .buildozer-venv
.buildozer-venv/bin/python -m ensurepip
uv pip install --python .buildozer-venv/bin/python \
  git+https://github.com/kivy/buildozer@76bac28545c66bbcc671d49aca553a747d69608e \
  legacy-cgi setuptools cython==0.29.34
. .buildozer-venv/bin/activate
buildozer android debug
```

The first build downloads Android SDK/NDK components and may take a while. If
the SDK manager fails while reading licenses, invoke it with the explicit SDK
root, for example:

```sh
sdkmanager --sdk_root="$ANDROID_SDK_ROOT" --licenses
```

The project targets Android API 36 (minimum API 24), packages Python 3.14.2
and Kivy 2.3.2, and builds ARM64 and 32-bit ARM variants. The python-for-android
`develop` branch and commit are pinned in `buildozer.spec` for Python 3.14
support and repeatable source selection. The verified build used Buildozer
commit `76bac28545c66bbcc671d49aca553a747d69608e`. No Android permissions are
requested. SQLite is stored in Kivy's private writable app directory, Android
backup is disabled, and the app does not require network access.

The generated debug APK is written to `bin/`. Install it on a USB-debugging
enabled device with:

```sh
adb install -r bin/app-0.1.0-arm64-v8a_armeabi-v7a-debug.apk
```

The Phase 6 APK was built and installed on a physical ARM Android device. The
four views, local persistence after restart, and task access with Wi-Fi off
were checked. It is a debug preview for direct testing, not a production-signed
release. Build settings are in `buildozer.spec`; see the
[Buildozer specification reference](https://buildozer.readthedocs.io/en/latest/specifications/)
and [python-for-android build options](https://github.com/kivy/python-for-android/blob/develop/doc/source/buildoptions.rst).
The tested APK SHA-256 is recorded in `CHANGELOG.md`.

## GitHub releases

Pushing a version tag starting with `v` starts
`.github/workflows/android-release.yml`. Use `vMAJOR.MINOR.PATCH` for a stable
release and append a SemVer prerelease suffix, such as `v0.1.0-rc.1`, for a
GitHub prerelease. The tag's base version must match both `pyproject.toml` and
`buildozer.spec`; update both before tagging a new version.

The workflow runs the locked pytest suite, builds the Android debug APK on
Ubuntu, and publishes the APK plus a SHA-256 file to the GitHub Release. A
hyphenated prerelease suffix marks the release as a prerelease automatically.
The APK is debug-signed for direct installation; this workflow does not use
production signing secrets or create a store-ready package.

## First preview release

See [CHANGELOG.md](CHANGELOG.md) for the `0.1.0` preview notes and the
remaining distribution steps. The repository does not currently declare a
software license; select and add one before publishing or redistributing the
source outside the intended private testing context.
