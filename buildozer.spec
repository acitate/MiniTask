[app]
title = MiniTask
package.name = app
package.domain = org.minitask
source.dir = src
source.include_exts = py,kv,png,jpg,atlas
version = 0.1.0
requirements = python3==3.14.2,hostpython3==3.14.2,kivy==2.3.2
orientation = portrait
fullscreen = 0

# The app uses only internal storage and does not need network access.
# Leave android.permissions unset to keep the manifest permission-free.
android.api = 36
android.minapi = 24
android.ndk = 29
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False

# Python 3.14 Android builds use python-for-android's current development branch.
p4a.branch = develop
