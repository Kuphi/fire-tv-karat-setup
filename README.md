# Fire TV karat setup

Set up root, Google Play/microG, Emotn Launcher and selected TV apps on supported karat Fire TV Sticks. Includes English and German interfaces and an optional update to Fire OS 8.1.8.2.

[English](README.md) · [Deutsch](README_DE.md)

## Recommended quick start

1. **Extract the complete setup ZIP** into a folder on your PC. If you also have `packages.zip`, extract its contents into `packages/`. The result should contain `packages/root/`, not `packages/packages/root/`. Missing files can also be downloaded during setup.
2. **Connect one supported Fire TV Stick by USB**, keep power stable, enable ADB debugging and accept the authorization on the TV. Have at least **12 GiB free on the PC** for backups.
3. **Start the main launcher** from the extracted folder:

   | Linux | Windows |
   |---|---|
   | `bash 00_setup.sh` | Run `00_setup.bat`, or enter `.\00_setup.bat` in PowerShell |

4. **Choose your language, then your setup:**

   | Enter | What happens |
   |---|---|
   | `ALL` | Run phases 1–5 without changing the Fire OS version |
   | `ALL U` | Run phases 1–5 and integrate the 8.1.8.2 update into phase 2 |
   | `U` | Update an existing setup later, without running phases 3–5 again |

5. **Follow the terminal and TV prompts.** Complete Magisk Direct Install when asked; type `RESUME` in the terminal afterward. Grant EmotnUI permissions using the remote. Keep USB and power connected during writes. To continue after an interruption, start the same main launcher in the same folder again.

> **Using Fire OS 8.1.5.8?** On a 4K Plus, the top row of Settings was cropped on this version; updating to 8.1.8.2 resolved it. If you see the same problem, use `ALL U` for a new setup or `U` for an existing one. The cause has not been confirmed, and the issue has not been established for every device on 8.1.5.8.

Root/unlock writes can permanently damage the device. The backup is created after unlocking and cannot protect against a failed unlock. See [compatibility](#compatibility) before starting.

## Choose what to run

The main menu runs selections in the required order and removes duplicates. Use spaces or commas, for example `1 2 3`, `3,4,5` or `U 3 4`. If a phase fails, later phases do not start.

| Option | Task | Linux launcher |
|---|---|---|
| 1 | Temporary root and OTA blocking | `01_temporary_root_and_disable_ota.sh` |
| 2 | Unlock, one-time backup, Post-OTA and permanent root with Magisk | `02_permanent_root_magisk.sh` |
| U | Optional update to Fire OS 8.1.8.2; combined with phase 2 when both are selected | Main menu |
| 3 | Google Play, microG, Zygisk Next, Vector and FakeGApps | `03_google_play_and_microg.sh` |
| 4 | Emotn Launcher, helpers and Vector scope | `04_emotn-launcher-setup.sh` |
| 5 | Select apps, install and optimize | `05_install_apps_and_optimize.sh` |

Every numbered launcher has matching Windows `.bat` and `.ps1` files. **The recommended entry point is always `00_setup`**, including when resuming. Phase 3 requires permanent root; phase 4 requires the configured framework/Vector.

### Optional update: U

`ALL` means phases 1–5; it does **not** include the firmware update. `ALL U` flashes firmware, Post-OTA and Magisk in one TWRP session before Google/microG setup, avoiding an intermediate Android boot.

You can select **only `U` later**. Existing verified unlock and PC-backup checkpoints are reused. The script preserves previously disabled modules and restores previously enabled Vector/microG promotion only after preinit and verifier checks. Phases 3–5 are not repeated.

The target is **Fire OS 8.1.8.2 / RS8182.3811N / 0032548774788**. Already installed 8.1.8.2 is not flashed again; newer firmware is not downgraded. Use the Amonet karat TWRP installed by this setup, not an unrelated recovery with the same version label.

See [UPDATE.md](UPDATE.md) for the full sequence, firmware hash, recovery rules and validation limits. A manual firmware change outside this workflow is not automatically adopted by rewriting old checkpoints.

## Language and command-line options

Choose **1 English** or **2 Deutsch** before setup and dependency installation. All selected phases inherit the language. Both languages use the same checkpoints and backups.

```bash
bash 00_setup.sh --lang en
bash 00_setup.sh --lang de --steps "ALL U"
bash 00_setup.sh --steps 5 --apps "1 2 6"
```

Windows accepts the same options:

```powershell
.\00_setup.bat --lang en
.\00_setup.bat --lang de --steps "ALL U"
```

Use `--serial SERIAL_NUMBER` when multiple USB devices are connected. Otherwise exactly one authorized USB Stick is detected automatically. Use `--help` for options. `FIRE_TV_LANG=en` or `FIRE_TV_LANG=de` sets a default; `--lang` overrides it. Noninteractive runs default to English.

## Compatibility

| Fire TV Stick | Model identifier |
|---|---|
| 4K Max, 2nd generation | `AFTKRT` |
| 4K, 2nd generation | `AFTKM` |
| 4K Plus | `AFTMA08C15` |

The device must identify as **`karat`** and match an exact build, incremental version and kernel combination in `SUPPORTED` in [karat.py](karat-automation/karat.py). A listed model alone is insufficient. Unknown firmware profiles remain blocked.

The manual firmware update and Settings fix were reported successful on a 4K Plus. Automated tests use mocked ADB; they do not establish hardware-tested compatibility for every model and firmware. First-generation Sticks, 4K Select and other device platforms are outside this workflow. No automatic bootrom/unbrick or downgrade procedure is included.

## Dependencies

Normal setup needs **Python 3.10 or newer**, **ADB / Android Platform Tools**, a USB data connection, authorized ADB debugging, stable power and internet access for missing downloads. Reserve at least **12 GiB free on the PC** before unlocking. No pip packages are required for normal setup.

### Linux

Launchers install missing Python/ADB using `tools/install-dependencies.sh`; this may require `sudo`.

| Distribution | Package manager | Packages |
|---|---|---|
| Ubuntu / Debian | `apt-get` | `python3`, `adb`, `curl`, `wget`, `unzip`, `ca-certificates` |
| Fedora | `dnf` | `python3`, `android-tools`, `curl`, `wget`, `unzip`, `ca-certificates` |
| Arch and derivatives | `pacman` | `python`, `android-tools`, `curl`, `wget`, `unzip`, `ca-certificates` |

Bash is required. Older distributions may need a newer Python installed separately. If ADB reports `no permissions`, check USB/udev rules; do not use permanent root ADB on the PC as a workaround.

### Windows

Native BAT/PowerShell/Python launchers are included; WSL and Git Bash are unnecessary.

- Missing Python is installed using `winget` with the Python 3.13 package. Without winget, install Python from [python.org](https://www.python.org/downloads/windows/) and enable PATH.
- Missing ADB is downloaded from Google's official Platform Tools ZIP into `tools/platform-tools`.
- An existing `wget.exe` is preferred for this download; otherwise PowerShell `Invoke-WebRequest` is used. The PowerShell `wget` alias is not GNU wget.
- Install a suitable USB/ADB driver separately if required. After installing Python, you may need a new terminal.

The separately used upstream amonet recovery tools have their own dependencies. They are not required by this normal workflow; follow upstream instructions if using them independently.

## Installation files and downloads

This setup ZIP contains scripts and **five helper APKs**. Root ZIPs, stock firmware, the Magisk APK, EmotnUI and Google APKs are obtained separately or downloaded when needed.

- [config/required-files.json](config/required-files.json): expected paths, URLs and available pinned hashes.
- [config/sources.local.json](config/sources.local.json): included default sources; editing is optional.
- [SOURCES.md](SOURCES.md): upstream projects and credits.

Existing matching files are reused. Archives, APK manifests and available pinned hashes are checked. Do not substitute another version's hash to make a mismatching file pass.

### Using packages.zip

If the archive directly contains `root`, `google-play` and `emotn`, extract it **into `packages/`**. If it already contains an outer `packages` folder, extract that into the setup folder instead.

```text
fire-tv-karat-setup/
├── 00_setup.sh / 00_setup.bat
├── karat-automation/
├── config/
└── packages/
    ├── root/
    │   ├── amonet-karat-v1.3.0.zip
    │   ├── ghostlock-karat-v1.0.4.zip
    │   ├── post-ota-karat-v1.0.0.zip
    │   └── Magisk-v30.7.apk
    ├── google-play/
    │   ├── zygisk-next.zip
    │   ├── vector.zip
    │   ├── fakegapps.apk
    │   ├── microg.apk
    │   ├── play-store-tv.apk
    │   └── microg-installer.zip
    └── emotn/
        ├── EmotnUI.apk
        └── helpers/
```

Do not extract the individual installation ZIPs. An additional `Magisk-v30.7.zip` is unused: setup uses the full APK and renames it during transfer for TWRP installation. For U, an existing firmware `.bin` can be renamed to `packages/root/FireOS-8.1.8.2.zip`; otherwise it is downloaded.

### If a download fails

A failed or blocked download opens a clear manual-download prompt instead of silently continuing. It shows the link, exact filename and destination. Download the file, place it as instructed and type **`RESUME`**. Missing or invalid files keep the prompt open; **`EXIT`** exits explicitly.

For pinned files, matching browser downloads in your usual `Downloads` folder can be verified and copied automatically after RESUME. Their original copies are preserved. XDA may require browser confirmation. The Play Store downloader follows the APKMirror version page's normal download steps using fresh keys; server blocks or expired links can still require manual download. This fallback also applies during `--dry-run`.

## What you need to do on the TV

| Stage | Your action |
|---|---|
| Root / update | Type the requested `ROOT`, `UNLOCK` or `UPDATE` confirmation in the terminal |
| Magisk | Complete **Install → Direct Install (Recommended)** when prompted; then enter `RESUME` in the terminal. The script handles rebooting |
| Built-in Zygisk | Normally nothing: if it is off, phase 3 continues automatically. If enabled, setup opens Magisk and asks you to disable it, then checks and reboots |
| FakeGApps | Enable it in Vector and scope it **only to System Framework / android** |
| microG | In Self-Check, verify **System spoofs signature**; enable Device registration and Cloud Messaging yourself |
| Emotn | Grant requested permissions with the remote; check display/navigation; confirm launcher selection when asked |
| Emotn helpers | Enable System Clock, Idle Timer and App Categories in Vector; scope them **only to Emotn UI** |
| Accounts / stores | Sign in and confirm store installations yourself |

Enter alone does not confirm a prompt. Keep Magisk's built-in Zygisk off; Zygisk Next provides Zygisk for this setup. Magisk preinit and Vector's SELinux rules are checked before relevant framework reboots.

Emotn System Clock follows the **Fire TV's timezone**, including later changes. It does not set Berlin time or change the device timezone. Set your own weather town; weather location is independent of the clock. Phase 4 replaces only the obsolete fixed-timezone clock helper when present.

## Select apps in phase 5

| Number | App | Preferred source |
|---|---|---|
| 1 | Netflix | Amazon Appstore |
| 2 | YouTube | Amazon Appstore |
| 3 | Prime Video | Amazon Appstore |
| 4 | Disney+ | Amazon Appstore |
| 5 | Wholphin | Official GitHub APK / Play Store |
| 6 | CX File Explorer | Play Store / matching local APK |

Enter `1 2 6`, `ALL`, `NONE` or `EXIT`. Existing selected apps are optimized without reinstalling; missing selected apps are installed first. Unselected apps are not installed or optimized.

Phase 5 always applies animation scales of **0.5** and optimizes Emotn. `NONE` performs only those actions. Apps still missing are listed at the end. Materialious, Aurora, F-Droid and WireGuard are not configured. **Emotn App Categories belongs to phase 4**, not the app menu.

## Resume, backups and cleanup

Start **the same main launcher in the same folder** after an interruption. The per-device saved plan retains remaining phases, app choices and relevant options. Explicit `--steps` starts a new selection. A failed phase blocks later phases; uncertain flash writes are never automatically replayed.

When replacing setup files, keep:

- `karat-automation/runtime/` — checkpoints, saved plans and technical logs;
- `backups/` — verified PC backups;
- `packages/` — existing installation files.

Completed verified unlock/backup stages are reused. Old Windows backup manifests with backslashes remain readable, with files and hashes still checked. Only a narrowly verified historical Post-OTA **preflight abort** can be recovered automatically from its original log; a started or unproven flash remains blocked. Do not clear `pending` by hand.

| Phase | Device cleanup |
|---|---|
| 1 | No `/sdcard` staging files; the running temporary su service is preserved |
| 2 | Setup-owned Magisk/Post-OTA files and the two setup-owned TWRP backup folders, after PC-backup verification |
| U | Setup-owned firmware/root files and Vector ZIP used for restoration, after update checks |
| 3 | Known Google/framework staging files and APK/APKM files under `/sdcard/Download/Downloader` |
| 4–5 | No root-backup/storage cleanup |

PC backups and unrelated TWRP backups are preserved. A failed phase does not run its final cleanup. Wi-Fi is restored after the OTA-block checks when Android is ready; failures warn and allow setup to continue. Wi-Fi is not changed in TWRP.

## Boot problems

The known conflict concerns the **Google package verifier**, not the vendor partition. Setup disables Google's verification receiver after Google APK installation, before promotion and before the relevant Android reboots. It requires `new state: disabled` and exactly one active receiver: `com.amazon.adep/.nimh.receiver.PackageVerificationReceiver`. The Play Store package stays enabled.

After six minutes without confirmed Android boot completion, diagnostic guidance appears. A timeout alone does not prove a verifier conflict. Invalid `xposed_file` labels or denied `dex2oat` execution can instead indicate missing Magisk preinit/Vector rules.

Keep USB connected, preserve logs and checkpoints, and see [MANUAL-REPAIR.md](MANUAL-REPAIR.md) and [UPDATE.md](UPDATE.md). Do not repeat flashes or delete backup state to bypass a failure.

## Preview and download test

Python 3.10+ must already be installed for device-free modes; these modes do not install dependencies.

```bash
# Appearance only: no downloads or device actions
bash 00_setup.sh --preview-only --steps "ALL U"

# Real downloads and file checks; device actions are simulated
bash 00_setup.sh --dry-run --steps "ALL U"

# Preview selected apps
bash 05_install_apps_and_optimize.sh --preview-only --apps "1 2 6"
```

Windows uses the matching `.bat` launchers with the same options. A download test creates local packages/logs and may ask for manual files. Store installs still need a device; simulated output is not a functional hardware test.

## Logs, validation and sharing

Normal output shows progress, status and required input. Downloads show bytes, speed and percentage when the server supplies a size. Local APK installation uses an activity indicator because Android supplies no installation percentage. Full technical output is saved in the displayed UTF-8 log under `karat-automation/runtime/`. Add `--verbose` for those details in the terminal; set `NO_COLOR=1` to disable colors.

Offline checks cover mocked ADB behavior, checkpoints, update ordering and both languages. Windows code paths are checked offline; native Windows and every device/firmware combination have not been hardware-tested. `SHA256SUMS` lists the release file hashes. See [UPDATE.md](UPDATE.md) for update-specific validation limits.

Before sharing or uploading to GitHub, exclude runtime, backups, accounts and personal configuration. Third-party APKs, firmware and helpers retain their respective licenses and redistribution terms; inclusion in a local setup does not grant redistribution rights. No personal town, account or device state is preconfigured in the shareable bundle.
