# MiniTask

MiniTask is a small, offline-first task planner for Android, built with Python
and Kivy. It has four views: Today, Tomorrow, Long-term, and All. Each task is
stored once; daily plans link to tasks, so edits and completion stay in sync.
Daily plans are manual, and unfinished tasks do not roll over automatically.

> **Vibe-coding disclosure:** This project was entirely vibe-coded and was
> created only to meet my personal needs. It is shared as-is, without any
> promise of support or suitability for other uses.

## Run on desktop

Requires Python 3.14+ and [UV](https://docs.astral.sh/uv/):

```sh
uv sync --locked
uv run minitask
```

To run the tests:

```sh
uv run pytest
```

The app stores its SQLite database in the platform's user data directory. Set
`MINITASK_THEME=light` or `MINITASK_THEME=dark` to select a desktop theme.

## Android

Android builds use Buildozer and python-for-android. On Ubuntu, follow the
[Buildozer Android installation guide](https://buildozer.readthedocs.io/en/latest/installation/)
and install OpenJDK 17. Then create an isolated build environment and build:

```sh
uv venv --python 3.14 .buildozer-venv
.buildozer-venv/bin/python -m ensurepip
uv pip install --python .buildozer-venv/bin/python \
  git+https://github.com/kivy/buildozer@76bac28545c66bbcc671d49aca553a747d69608e \
  legacy-cgi setuptools cython==0.29.34
. .buildozer-venv/bin/activate
buildozer android debug
```

The first build downloads the Android SDK and NDK and can take a while. The
APK is written to `bin/`. The app stores data in its private app directory and
works offline. The included build creates a debug-signed APK for direct testing,
not a production or app-store package.
