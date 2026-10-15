#!/usr/bin/env bash
set -euo pipefail
ui_message() {
    if [[ ${FIRE_TV_LANG:-en} == de ]]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi
}
base=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
flow=$1; shift
# Select language before dependency installation; children inherit the choice.
for ((i=1; i<=$#; i++)); do
    arg=${!i}
    if [[ $arg == --lang ]]; then
        next=$((i+1)); [[ $next -le $# ]] || { echo '--lang requires en or de / --lang benötigt en oder de' >&2; exit 2; }
        export FIRE_TV_LANG=${!next}
    elif [[ $arg == --lang=* ]]; then export FIRE_TV_LANG=${arg#--lang=}; fi
done
if [[ -z ${FIRE_TV_LANG:-} ]]; then
    if [[ -t 0 ]]; then
        echo; echo 'Choose language / Sprache wählen'; echo '[1] English'; echo '[2] Deutsch'; echo 'EXIT = exit / beenden'
        while true; do
            read -r -p '1 / 2 → ' language_choice || exit 0
            case "$language_choice" in
                1|en|English) export FIRE_TV_LANG=en; break ;;
                2|de|Deutsch) export FIRE_TV_LANG=de; break ;;
                EXIT|exit) exit 0 ;;
                *) echo 'Please choose 1 or 2 / Bitte 1 oder 2 wählen.' ;;
            esac
        done
    else export FIRE_TV_LANG=en; fi
fi
[[ $FIRE_TV_LANG == en || $FIRE_TV_LANG == de ]] || { echo 'Language must be en or de / Sprache muss en oder de sein' >&2; exit 2; }
export PYTHONDONTWRITEBYTECODE=1
engine="$base/karat-automation/karat.py"
if [[ $flow == menu ]]; then engine="$base/karat-automation/setup_menu.py"; fi
if [[ $flow == apps ]]; then engine="$base/karat-automation/install_apps_and_optimize.py"; fi
[[ -f $engine ]] || { ui_message 'The complete package is missing.' 'Das vollständige Paket fehlt.' >&2; exit 2; }
export PATH="$base/tools/platform-tools:$PATH"
need_adb=true
dry_run=false
for arg in "$@"; do
    [[ $arg != --prepare-only && $arg != --help && $arg != --dry-run && $arg != --preview-only ]] || need_adb=false
    [[ $arg != --dry-run && $arg != --preview-only ]] || dry_run=true
done
if $dry_run && ! command -v python3 >/dev/null; then
    ui_message 'Install Python >=3.10 for the preview; dry run does not install dependencies.' 'Für die Vorschau Python >=3.10 installieren; im Dry Run werden keine Abhängigkeiten installiert.' >&2
    exit 2
fi
if ! command -v python3 >/dev/null || { $need_adb && ! command -v adb >/dev/null; }; then
    bash "$base/tools/install-dependencies.sh"
fi
python3 -c 'import sys;assert sys.version_info >= (3,10), "Python >= 3.10 required"'
if [[ $flow == apps || $flow == menu ]]; then exec python3 "$engine" --base "$base" "$@"; fi
exec python3 "$engine" "$flow" --base "$base" "$@"
