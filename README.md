# Fire TV karat – shareable setup bundle

[English](README.md) · [Deutsch](README_DE.md)

## Choose your language

Start `00_setup.bat` on Windows or `bash 00_setup.sh` on Linux. Before setup or dependency installation, choose **1 English** or **2 Deutsch**. All selected phases inherit this choice. Direct phase launchers and Python entry points offer the same choice.

To skip the prompt, use `--lang en` or `--lang de`. Noninteractive runs default to English. `FIRE_TV_LANG=en` or `FIRE_TV_LANG=de` can also set the default; an explicit `--lang` takes priority.

```bash
bash 00_setup.sh --lang en
bash 00_setup.sh --lang de --preview-only --steps ALL
```

Windows:
```text
00_setup.bat --lang en
00_setup.bat --lang de
```

Both languages share one engine, checkpoints, backups and setup plans. Switching languages does not restart completed work. When updating, keep runtime state, PC backups and packages. Historical German logs remain readable by the resume logic. English is the default documentation; German instructions are in `README_DE.md`.


Updated: 2026-10-14. Includes scripts and five helper APKs.
No personal logs, checkpoints, serial numbers, backups, accounts or VPN configurations are included.

## Optional firmware update: U

! If you have version 8.1.5.8 it is recommended to update. Otherwise your settings screen will not show the upper row, due to the ad banner being removed !

Options **1–5** remain unchanged. Choose **ALL U** to include Fire OS **8.1.8.2**: the firmware update is integrated into phase 2, before Google/microG. Firmware, Post-OTA and Magisk are flashed in one TWRP session. **U** also works on its own. Previously active Vector/microG modules are restored only after Magisk preinit and verifier checks. Restart the same main menu to resume.

See [UPDATE.md](UPDATE.md) for the sequence, checkpoints, firmware hash and validation limits. Preview: `bash 00_setup.sh --preview-only --steps "ALL U"` (Windows: `00_setup.bat` with the same arguments).

## Main menu and execution order

Linux: `bash 00_setup.sh` · Windows: `00_setup.bat`.
Select **1,2,3**, **3,4,5** or **ALL**. Duplicate selections are removed and phases run in order.
The menu uses the same USB-connected Fire TV Stick for every selected phase. If a phase fails, later phases do not start.

| Phase | Linux launcher | Task |
|---|---|---|
| 00 | `00_setup.sh` | Main menu / phase selection |
| 01 | `01_temporary_root_and_disable_ota.sh` | Temporary root and OTA blocking |
| 02 | `02_permanent_root_magisk.sh` | Unlock, one-time backup, Post-OTA, Magisk |
| 03 | `03_google_play_and_microg.sh` | Google Play, microG, Zygisk Next, Vector, FakeGApps |
| 04 | `04_emotn-launcher-setup.sh` | Emotn Launcher |
| 05 | `05_install_apps_and_optimize.sh` | Install and optimize selected apps |

Every launcher has matching native Windows `.ps1` and `.bat` versions. Phases can also be launched directly.

```bash
bash 00_setup.sh --steps 1,2,3 --dry-run
bash 00_setup.sh --steps ALL --preview-only
bash 03_google_play_and_microg.sh --dry-run
```

Phase 01 asks for `ROOT` when temporary root must be obtained. It does not unlock the bootloader or create a backup.
OTA and OTA Override are disabled and checked. Temporary root is lost on reboot, so it is not recorded as permanently completed.
Phase 02 can obtain temporary root itself and still requires `UNLOCK` before unlocking.
Phase 03 requires permanent root with Magisk 30.7; phase 04 requires the configured framework/Vector.
The one-time backup and existing flash checkpoints are preserved. The Google phase does not create another backup.

Extract the complete bundle. Launchers find the bundle directory even when started from another working directory.
Exactly one authorized USB device is detected automatically. With multiple devices, add `--serial SERIAL_NUMBER`.
PowerShell/BAT launchers accept the same options. Use `--help` to show options.
Root phases and Emotn support `--prepare-only` for file checks/downloads without device changes.
Logs and checkpoints are created in `karat-automation/runtime` when used. Do NOT include them when sharing the bundle.

## Dependencies and installation

Python **>=3.10** (standard library only; no pip needed for normal setup), Android Platform Tools/ADB,
a USB data cable, authorized USB debugging, stable power and internet access for missing downloads.
Before unlocking, reserve at least **12 GiB of free PC storage** for backups.
Linux requires Bash. Windows uses native Python/PowerShell/BAT launchers; WSL and Git Bash are unnecessary.

Linux launchers install missing Python/ADB through `tools/install-dependencies.sh`:

| Distribution | Package manager | Packages |
|---|---|---|
| Ubuntu / Debian | apt-get | python3, adb, curl, wget, unzip, ca-certificates |
| Fedora | dnf | python3, android-tools, curl, wget, unzip, ca-certificates |
| Arch / derivatives | pacman | python, android-tools, curl, wget, unzip, ca-certificates |

This may require sudo. Old distributions with Python <3.10 need a newer Python version.
For `no permissions`, check your distribution's USB/udev rules; do not blindly run ADB permanently as root.

Windows installs Python 3.13 using winget if needed. If winget is unavailable, install Python from python.org and enable PATH.
ADB comes from Google's official Platform Tools ZIP and is extracted into `tools/platform-tools`.
An existing **wget.exe** is preferred; otherwise PowerShell `Invoke-WebRequest` is used.
The PowerShell `wget` alias is not GNU wget and is not used for this download.
Install a suitable USB/ADB driver separately if necessary; the scripts do not install arbitrary drivers.
After the first Python installation, you may need to open a new terminal.
Native Windows hardware tests were not performed here; platform-specific code paths were checked offline.

Optional external amonet recovery tools are not part of the normal workflow. Their Python dependencies
(including pyserial, pycryptodome, PyYAML, future and iso8601) apply only when using those tools separately.
Follow their upstream instructions; do not install old requirements globally.

## Devices and firmware

| Model | Identifier | Bundle status |
|---|---|---|
| Fire TV Stick 4K Max (2nd Gen) | AFTKRT | Existing workflow with offline regression tests |
| Fire TV Stick 4K (2nd Gen) | AFTKM | Identifier added; no independent hardware tests |
| Fire TV Stick 4K Plus (2025) | AFTMA08C15 | Identifier added; no independent hardware tests |

TWRP upstream identifies all three as karat/MT8696 devices. Detection accepts only `karat`, these three model identifiers
and the EXACT build/incremental/kernel combinations in `SUPPORTED` in `karat.py`.
The existing 15 firmware profiles were not extended with unverified builds. GhostLock documentation describes its karat target
as 4K Max; accepting all model identifiers does not prove hardware-tested root support for every firmware on every model.
Unknown profiles remain blocked. 4K Select, first-generation devices, other SoCs and Android/Vega variants are unsupported.
No downgrade or automatic bootrom/unbrick attempts are included.

## Required external installation files

Root ZIPs, EmotnUI and third-party APKs are not included in this script ZIP.
`config/required-files.json` lists paths, versions, pinned SHA256 hashes and download URLs.
The three root ZIPs and EmotnUI use the supplied URLs. Each phase automatically uses known HTTPS URLs for missing files;
archives, manifests and pinned hashes are checked after download. Supply files manually when no URL is available.
The real `config/sources.local.json` is included with the available default links; editing it is optional.
The example file is only a template. Pinned hashes must not be replaced with hashes from other versions.

Required paths include:

- `packages/root/amonet-karat-v1.3.0.zip`
- `packages/root/ghostlock-karat-v1.0.4.zip`
- `packages/root/post-ota-karat-v1.0.0.zip`
- `packages/emotn/EmotnUI.apk`
- `packages/google-play/play-store-tv.apk` — TV variant `com.android.vending`, version 52.0.20-24.

The Play Store downloader starts from the stable APKMirror version page and follows public download buttons using fresh keys,
a normal cookie session and matching Referer headers. Old download keys are not stored. The resulting APK is checked by SHA256 and manifest.
If automatic download fails, open the page shown in `config/required-files.json` and place the APK at the required path.

Magisk 30.7, Zygisk Next 1.5.0, Vector 2.2, FakeGApps 6.6, microG 0.3.15.250932 and
microG Installer Revived Again 1.1.2 have sources in the scripts. Root ZIPs were not obtained from unrelated APK/ZIP portals.

## Workflow and confirmations

Phase 02 requires `UNLOCK` before the root/unlock attempt. GhostLock attempts temporary root at most twice,
with a verified reboot between attempts. Bootloader/IDME/flash writes are never retried automatically.
Rooting can permanently brick the device; backups created afterward cannot protect against a failed unlock.
Keep USB and power connected during writes.

The full Magisk app is installed locally and its installed APK hash is verified.
After Direct Install finishes, type `RESUME` in the terminal. The script reboots the Stick, waits for Android, verifies root, Magisk 30.7 and the full app, then cleans up. You do not need the Reboot button in Magisk. Restarting the main script also picks up this reboot step from older completed phase-2 checkpoints.
If necessary, a local repair is attempted, followed by manual Wi-Fi installation of the same v30.7 APK.
`RESUME` continues; `EXIT` ends the prompt. Enter alone does not confirm anything.
Keep Magisk built-in Zygisk OFF; keep Zygisk Next and Vector enabled.
Scope FakeGApps ONLY to System Framework/android. Check microG Self-Check; enable Device registration and Cloud Messaging yourself.
Set up accounts yourself.

### Verifier conflict and boot timeout

This concerns the **Google package verifier**, not the vendor partition:
`com.android.vending/com.google.android.finsky.verifier.impl.PackageVerificationReceiver`.
The script disables it immediately after Google APK installation, before promotion and directly before the microG reboot.
The output must end with `new state: disabled`, and exactly one receiver must remain:
`com.amazon.adep/.nimh.receiver.PackageVerificationReceiver`.
Play Store remains enabled and its system promotion is retained. The verifier is checked again after boot.

This reduces the known conflict but cannot guarantee a successful boot: package scanning may change state,
and unrelated boot failures are possible. After six minutes without confirmed boot completion, repair instructions appear.
No further flash starts automatically. See `MANUAL-REPAIR.md`.

### Cleanup after the three root phases

- 01 creates no temporary files on `/sdcard`. GhostLock files are in `/data/local/tmp`; the running su daemon is not deleted.
- 02 removes Magisk/Post-OTA ZIPs from `/sdcard` and both setup-owned TWRP device backups only after verifying PC copies and SHA256 hashes. Other backups and PC files are preserved.
- 03 removes known Google/framework staging files and APK/APKM files in `/sdcard/Download/Downloader`. The backup is not recreated or deleted again.
- Empty directories are removed; unrelated TWRP backups are never deleted wholesale.
- 04/05 do not perform this storage cleanup.

For adopted root installations without verified PC backups, backup deletion remains blocked.
A failed phase does not run its final cleanup.

### Emotn and apps

04 installs Emotn and asks you to confirm home launcher selection and Vector module scope.
Set **your own town** for weather. Emotn System Clock follows the Fire TV device timezone and reacts to timezone changes. It does not change the weather town or the device timezone. No personal cities or accounts are preconfigured.

05 sets animation scales to 0.5, skips installation of existing apps, installs selected missing apps and then runs `compile -m speed -f`.
Netflix, YouTube, Prime Video and Disney+ prefer Amazon Appstore. Wholphin uses its official GitHub release where possible.
CX uses a matching local APK or Play Store. Materialious, Aurora, F-Droid and WireGuard are not configured at all.
Confirm store installations yourself, then type `RESUME`; missing apps are listed at the end.
Emotn App Categories is installed in phase 4 with the launcher helpers. Enable it in Vector and scope it ONLY to Emotn UI. Phase 5 contains six app choices.
The launcher restarts at the end.

## Testing and sharing

```bash
python3 -m unittest discover -s karat-automation -p 'test_*.py' -v
```

Windows: use `py -3 -m unittest ...`. `SHA256SUMS` contains checksums for the finished bundle.
Tests are offline tests with mocked ADB, not real USB, Windows, flash or device tests.
After using the bundle, do not share runtime files, backups, personal source configuration or account data.
The five helper APKs came from the supplied package; their hashes were checked.
Third-party downloads and helpers remain subject to their respective usage/redistribution terms.
See `SOURCES.md`. No root or boot success guarantee is claimed.

## Download dry run without a connected Stick

`--dry-run` really downloads required files, checks archives/manifests/hashes and then shows simulated device output.
Verified existing files are reused. Downloads and logs are saved locally; no ADB or device changes occur.
Default links are in `FILES` in `karat-automation/karat.py`; a custom sources.local.json is not required.
Empty URLs in older configurations do not override defaults. HTTP error messages identify the affected file.

```bash
bash 02_permanent_root_magisk.sh --dry-run
bash 04_emotn-launcher-setup.sh --dry-run
bash 05_install_apps_and_optimize.sh --dry-run
```

To preview appearance only, without downloads or file writes:

```bash
bash 02_permanent_root_magisk.sh --preview-only
bash 04_emotn-launcher-setup.sh --preview-only
bash 05_install_apps_and_optimize.sh --preview-only
bash 02_permanent_root_magisk.sh --preview-only --dry-run-scenario boot-timeout
```

Windows: use matching `.bat` launchers with the same options. Python >=3.10 must already be installed for device-free modes.
Store installations require a device; the app dry run lists them as missing.
Device results are simulated, not actual functional tests. Download URLs may expire or be blocked by servers.

## When automatic download fails

HTTP 403/404, expired links or HTML instead of an APK trigger a clearly visible manual download prompt.
The script shows the link, filename and absolute destination folder in four steps.
Place the file at the requested path, do not extract ZIPs, and type `RESUME` to check it again.
Missing or incorrect files keep the prompt open. `EXIT` explicitly exits; noninteractive runs show instructions for resuming.
This also applies to download dry runs. Download-site protections are not bypassed.
Manual Play Store page:
https://www.apkmirror.com/apk/google-inc/google-play-store-android-tv/google-play-store-android-tv-52-0-20-release/google-play-store-android-tv-52-0-20-24-8-pr-937697325-4-android-apk-download/

### XDA browser fallback

A direct XDA request returned `403` with `cdn-challenge: true`: the site requires browser confirmation.
This also affects curl; unattended download is unavailable while the challenge is active.
In an interactive terminal, the script opens the link in your usual browser. Complete the confirmation and download the ZIP.
Save it in `~/Downloads`, then type `RESUME`. A matching filename (including browser suffixes such as `(1)`) is copied into
its package folder only if the pinned SHA256 matches. Unmatched files are untouched; the original download is not deleted.
For another download folder, use the explicitly displayed destination path.
Challenge cookies are not exported and anti-bot restrictions are not bypassed.
For offline root setup, place the three original ZIPs in `packages/root` beforehand.

### Verified direct Play Store download (2026-10-13)

The APKMirror version page was resolved through its normal download steps without a browser.
The live download was 66,201,277 bytes with SHA256
`16625b025c342c3badb63c60ba4158291863d21fa8bb7e6b16899144ab6037b6`.
Its manifest confirmed `com.android.vending`, versionCode `85202008`.
The APK was downloaded for verification only and is not redistributed in this script ZIP.
XDA root ZIPs still have a browser challenge. No alternative approved direct source for the same files was found;
those downloads have not been confirmed as fixed.

## Using a separate packages.zip

This bundle includes scripts and helpers only. Download the separately supplied `packages.zip` and
**extract its contents into the `packages` folder**. The resulting structure must be:

```text
fire-tv-karat-setup/
  00_setup.sh (or .bat)
  packages/
    root/amonet-karat-v1.3.0.zip
    root/ghostlock-karat-v1.0.4.zip
    root/post-ota-karat-v1.0.0.zip
    root/Magisk-v30.7.apk
    root/Magisk-v30.7.zip
    google-play/fakegapps.apk
    google-play/microg-installer.zip
    google-play/microg.apk
    google-play/play-store-tv.apk
    google-play/vector.zip
    google-play/zygisk-next.zip
    emotn/EmotnUI.apk
    emotn/helpers/ (the five helper APKs)
```

Linux, from the bundle directory:

```bash
mkdir -p packages
unzip -n packages.zip -d packages
```

Windows PowerShell, from the bundle directory:

```powershell
Expand-Archive -LiteralPath .\packages.zip -DestinationPath .\packages
```

These commands assume that packages.zip directly contains `root`, `google-play` and `emotn`.
If it already contains an outer `packages` folder, extract that into the bundle directory instead.
**Do not create `packages/packages/root`.**
Existing files take precedence over web downloads; archives, versions and pinned SHA256 hashes are still checked.
An optional `Magisk-v30.7.zip` is unused: the script uses the full APK and renames it only during transfer for flashing.

## App selection in phase 05

```bash
bash 05_install_apps_and_optimize.sh
```

Enter a selection such as **1 2 6**:

| Number | App | Source |
|---|---|---|
| 1 | Netflix | Amazon Appstore |
| 2 | YouTube | Amazon Appstore |
| 3 | Prime Video | Amazon Appstore |
| 4 | Disney+ | Amazon Appstore |
| 5 | Wholphin | Official GitHub APK / Play Store |
| 6 | CX File Explorer | Play Store / matching local APK |

`ALL` selects all apps. `NONE` applies only animation settings and Emotn optimization. `EXIT` exits without setup.
Unselected apps are neither installed nor optimized. Already installed selected apps are only optimized.
Animation settings and Emotn optimization remain part of phase 05.

```bash
bash 05_install_apps_and_optimize.sh --apps "1 2 6"
bash 00_setup.sh --steps 5 --apps "1 2 6"
bash 05_install_apps_and_optimize.sh --preview-only --apps "1 2 6"
```

Windows: use matching `.bat` launchers with the same options.
Materialious, Aurora, F-Droid and WireGuard are removed from all setup/download lists. `--extras` was removed;
existing installations of these apps are untouched.

## Clear terminal output

By default, the terminal shows progress, verified files, installation status, warnings and required input.
Full ADB/aapt output, complete SHA256 hashes and host details remain in the UTF-8 technical log in `karat-automation/runtime`.
The log path is displayed. Use `--verbose` to show every detail in the terminal too:

```bash
bash 00_setup.sh --verbose
bash 03_google_play_and_microg.sh --verbose
```

Colors are enabled only in a suitable interactive terminal. Redirected output contains no ANSI control codes.
Set `NO_COLOR=1` to disable colors. Windows launchers offer the same options.
Prompts clearly show accepted input: `ROOT`, `UNLOCK`, `RESUME`, `EXIT`, or menu numbers.
Empty or invalid confirmations do not start a step; the prompt remains open.
Interactive `--dry-run` and `--preview-only` modes also show selection menus; use `--steps`/`--apps` to specify choices directly.
Script messages and documentation are available in English and German. Bundled third-party APKs are unchanged and retain their own supported languages.

## Automatic resume through the main launcher

To continue, use the main launcher again: Windows `00_setup.bat`, Linux `bash 00_setup.sh`. It detects the USB-connected Stick and saves the selected phase sequence per device in `karat-automation/runtime`. After an interruption, it continues with the remaining phases. App selection and relevant setup options are retained. Completed unlock/backup stages are not repeated. Explicit `--steps` starts a new selection.

For an older checkpoint with `pending=postota` or another unfinished permanent-root stage, the main launcher detects phase 2 automatically. Older versions did not save menu choices, so additional phases are not invented or added automatically. Newly saved setup plans retain the complete originally selected remaining sequence.

`pending=postota` is now set immediately before the actual `twrp install`, after backup verification, byte checks and verified transfer. A failed preflight no longer creates an uncertain flash checkpoint.

An older `pending=postota` can be resumed from a complete preflight-abort log belonging to the same Stick and the known German release dated 2026-10-13 16:06:40. The main launcher automatically searches the runtime directory for that earlier log. It must show an explicit abort without a started installer command. TWRP and PC backups are checked, and the checkpoint is backed up before resetting pending. Post-OTA is not marked complete: its preflight checks run again. A byte check that still fails requires investigation. Historical German log parsing remains supported in this English release.

A flash that actually started, missing/truncated logs or unknown script versions are not retried automatically. A diagnostic log showing completed backups alone does not prove a successful Post-OTA step. The output identifies the earlier error log and original error where possible. Do not clear `pending` manually.

Extract updated files over the existing installation. Keep `karat-automation/runtime`, PC backups and `packages`. For multiple devices, add `--serial SERIAL_NUMBER`. Resume does not guarantee a successful Post-OTA flash when the original cause is still unknown.

## Windows backup paths

Older Windows versions stored relative paths in `verified.json` with backslashes, but the Boot/Data/System completeness check expected forward slashes. This release accepts both forms and writes new relative backup paths with `/`. Existing manifests are not overwritten; files and their SHA256 hashes are still checked. A genuinely missing or modified backup remains blocked.

Continue through `00_setup.bat` or `bash 00_setup.sh` as usual. Keep runtime state, existing PC backups and packages when updating.

## Clock follows the Fire TV timezone

Phase 04 now installs `Emotn-System-Clock.apk` instead of the fixed Berlin clock. It reads `persist.sys.timezone` at each timezone lookup, handles Android timezone-change broadcasts and refreshes the foreground launcher, or refreshes it on return from the background. If the property is unavailable, it uses Android's current default timezone. No device timezone is written or required. Weather location remains independent.

The new package is `local.karat.emotnsystemclock`. Phase 04 removes only the obsolete `local.karat.emotnclock` helper and installs the replacement. In Vector, enable **Emotn System Clock**, scoped only to **Emotn UI**. The new scope checkpoint ensures this prompt appears when upgrading an existing setup. The launcher restarts once to apply the module; later timezone changes do not require rerunning setup.

The updated clock APK is bundled directly; no helper-source folder or build toolchain is needed for installation. It targets Emotn UI 1.1.0.2. APK signatures and offline behavior tests passed; physical Fire TV behavior remains to be verified.

## GhostLock root-service readiness

The `ROOTED` proof can appear before the embedded su client/daemon is ready. Setup now waits for an actual `uid=0` result, probing both `su` and `/data/local/tmp/su` without treating a missing client (exit 127) as an immediate fatal error. The selected client is then used for temporary-root OTA and unlock commands.

The main script can resume `pending=ghostlock`. It first checks for a working root service. If unavailable, a verified reboot discards the temporary attempt before the remaining retry. The two-attempt limit is retained across restarts; other pending write stages are never cleared by this recovery. Keep runtime state, backups and packages when updating, and use `00_setup.bat` or `bash 00_setup.sh` as usual.

Downloads show a live bar with bytes, percentage when the server supplies a file size, speed and elapsed time. Downloads with no reported size show bytes received. Local APK installations show an animated activity bar until ADB finishes; Android does not supply an installation percentage. App-store downloads remain visible on the TV. The microG self-check prompt opens microG settings automatically; select Self-Check on the TV.

Wi-Fi is restored at the end of phase 1 after both OTA update packages are confirmed disabled. Phase 2 checks those packages again and enables Wi-Fi after Android returns from Post-OTA, including on resume. No Wi-Fi changes are attempted in TWRP. If enabling fails, a visible warning is shown and setup continues; connection uses the network settings already saved on the Stick.

Phase 3 automatically checks Magisk built-in Zygisk. If it is off (the physical-device default), setup continues without opening Magisk or asking for RESUME. Only if it is enabled does the script open Magisk, ask you to disable it, recheck and reboot before installing the framework.
