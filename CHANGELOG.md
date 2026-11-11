# Changelog

Notable changes to MiniTask are recorded here.

## 0.1.0 — First preview

- Added Today, Tomorrow, Long-term, and All views with bottom navigation.
- Added persistent tasks, nested subtasks, notes, optional deadlines, and
  independent completion state.
- Added manual, date-specific daily assignments that reference existing tasks,
  with manual ordering and no automatic deadline scheduling or rollover.
- Added local SQLite persistence, schema versioning, and rollback-safe
  transactions.
- Added task details, hierarchy expansion, assignment picker, deletion
  confirmation, empty states, and light/dark Adwaita-inspired themes.
- Added offline Android packaging for ARM64 and ARM devices.

### Validation

- Automated suite: 40 tests passed.
- Android debug APK built, installed, and exercised on a physical Android 12
  ARM device. The four primary views, restart persistence, and offline access
  were checked.
- Tested debug APK: `bin/app-0.1.0-arm64-v8a_armeabi-v7a-debug.apk` (40 MB),
  SHA-256 `285ddeb8b1e7a45adfb0e82b4822fe527b80184cbcb3e8b65b079d50f6be7c51`.
- This preview APK is debug-signed and intended for direct testing. A
  production signing key, distribution channel, and software license have not
  been configured.
