#!/usr/bin/env bash
# Explicit reversible launcher rollback, never firmware/partition restoration.
set -euo pipefail
adb -d shell pm enable --user 0 com.amazon.firehomestarter
adb -d shell pm enable --user 0 com.amazon.tv.launcher
adb -d shell pm enable --user 0 com.amazon.tv.launcher/.ui.HomeActivity_vNext
adb -d shell cmd package set-home-activity --user 0 com.amazon.tv.launcher/.ui.HomeActivity_vNext
adb -d shell am start -n com.amazon.tv.launcher/.ui.HomeActivity_vNext
