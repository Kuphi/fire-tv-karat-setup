#!/usr/bin/env bash
set -euo pipefail
ui_message() {
    if [[ ${FIRE_TV_LANG:-en} == de ]]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi
}
source /etc/os-release
as_root=()
if [[ $EUID -ne 0 ]]; then as_root=(sudo); fi
case "${ID:-} ${ID_LIKE:-}" in
  *ubuntu*|*debian*) "${as_root[@]}" apt-get update; "${as_root[@]}" apt-get install -y python3 adb curl wget unzip ca-certificates ;;
  *fedora*) "${as_root[@]}" dnf install -y python3 android-tools curl wget unzip ca-certificates ;;
  *arch*) "${as_root[@]}" pacman -S --needed --noconfirm python android-tools curl wget unzip ca-certificates ;;
  *) ui_message 'Distribution is not automatically supported: install Python >=3.10 and adb manually.' 'Distribution nicht automatisch unterstützt: Python >=3.10 und adb manuell installieren.' >&2; exit 2 ;;
esac
