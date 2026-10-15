# Fire-TV-karat-Setup

Root, Google Play/microG, Emotn Launcher und ausgewählte TV-Apps auf unterstützten karat-Fire-TV-Sticks einrichten. Mit deutscher und englischer Oberfläche sowie optionalem Update auf Fire OS 8.1.8.2.

[English](README.md) · [Deutsch](README_DE.md)

## Empfohlener Schnellstart

> **Vor dem Start: Fire OS 8.1.5.8 oder älter**
> Das Entfernen des Werbebanners während dieses Setups kann auf diesen Versionen die obere Reihe der Fire-TV-Einstellungen abschneiden. Das ist nicht auf den 4K Plus beschränkt; es kann jedes unterstützte Gerät mit 8.1.5.8 oder älter betreffen. Für eine neue Einrichtung **`ALL U`**, für eine bestehende Einrichtung **`U`** wählen, um auf Fire OS 8.1.8.2 zu aktualisieren. Im gemeldeten Fall hat dieses Update das Problem behoben.

1. **Das vollständige Setup-ZIP** in einen Ordner auf dem PC entpacken. Falls du außerdem `packages.zip` hast, dessen Inhalt nach `packages/` entpacken. Richtig ist `packages/root/`, nicht `packages/packages/root/`. Fehlende Dateien können auch während des Setups heruntergeladen werden.
2. **Einen unterstützten Fire TV Stick per USB anschließen**, für stabile Stromversorgung sorgen, ADB-Debugging aktivieren und die Autorisierung am TV bestätigen. Auf dem PC mindestens **12 GiB freien Speicher** für Backups bereithalten.
3. **Im entpackten Ordner das Hauptskript starten:**

   | Linux | Windows |
   |---|---|
   | `bash 00_setup.sh` | `00_setup.bat` starten oder in PowerShell `.\00_setup.bat` eingeben |

4. **Sprache und anschließend den Ablauf wählen:**

   | Eingabe | Ergebnis |
   |---|---|
   | `ALL` | Phasen 1–5 ohne Änderung der Fire-OS-Version |
   | `ALL U` | Phasen 1–5; Update auf 8.1.8.2 wird in Phase 2 integriert |
   | `U` | Bestehende Einrichtung später aktualisieren, ohne Phasen 3–5 erneut auszuführen |

5. **Den Hinweisen im Terminal und am TV folgen.** Magisk Direct Install bei Aufforderung abschließen und danach im Terminal `RESUME` eingeben. EmotnUI-Berechtigungen mit der Fernbedienung erteilen. Während Schreibvorgängen USB und Strom angeschlossen lassen. Nach einer Unterbrechung dasselbe Hauptskript im selben Ordner erneut starten.


Root-/Unlock-Schreibvorgänge können das Gerät dauerhaft beschädigen. Das Backup entsteht nach dem Unlock und schützt nicht vor einem fehlgeschlagenen Unlock. Vor Beginn die [Kompatibilität](#kompatibilität) prüfen.

## Ablauf auswählen

Das Hauptmenü sortiert die Auswahl in die erforderliche Reihenfolge und entfernt Duplikate. Leerzeichen oder Kommas verwenden, etwa `1 2 3`, `3,4,5` oder `U 3 4`. Bei einem Fehler werden spätere Phasen nicht gestartet.

| Option | Aufgabe | Linux-Starter |
|---|---|---|
| 1 | Temporäres Root und OTA-Sperre | `01_temporary_root_and_disable_ota.sh` |
| 2 | Unlock, einmaliges Backup, Post-OTA und permanentes Root mit Magisk | `02_permanent_root_magisk.sh` |
| U | Optionales Update auf Fire OS 8.1.8.2; bei gemeinsamer Auswahl mit Phase 2 kombiniert | Hauptmenü |
| 3 | Google Play, microG, Zygisk Next, Vector und FakeGApps | `03_google_play_and_microg.sh` |
| 4 | Emotn Launcher, Helper und Vector-Zuordnung | `04_emotn-launcher-setup.sh` |
| 5 | Apps auswählen, installieren und optimieren | `05_install_apps_and_optimize.sh` |

Zu jedem nummerierten Starter gibt es Windows-`.bat` und `.ps1`. **Empfohlener Einstieg bleibt immer `00_setup`**, auch zum Fortsetzen. Phase 3 benötigt permanentes Root; Phase 4 das eingerichtete Framework/Vector.

### Optionales Update: U

`ALL` bedeutet Phasen 1–5 und enthält **kein** Firmwareupdate. `ALL U` installiert Firmware, Post-OTA und Magisk in einer TWRP-Sitzung vor Google/microG; ein Android-Start dazwischen entfällt.

Du kannst **später nur `U` auswählen**. Vorhandene geprüfte Unlock- und PC-Backup-Checkpoints werden wiederverwendet. Zuvor deaktivierte Module bleiben deaktiviert. Zuvor aktive Vector-/microG-Promotion-Module werden erst nach Preinit- und Verifier-Prüfungen wiederhergestellt. Phasen 3–5 werden nicht wiederholt.

Ziel ist **Fire OS 8.1.8.2 / RS8182.3811N / 0032548774788**. Bereits installiertes 8.1.8.2 wird nicht erneut geflasht; neuere Firmware nicht heruntergestuft. Das durch dieses Setup installierte Amonet-karat-TWRP verwenden, keine fremde Recovery mit lediglich gleicher Versionsanzeige.

[UPDATE_DE.md](UPDATE_DE.md) beschreibt Reihenfolge, Firmware-Hash, Wiederaufnahme und Prüfgrenzen. Ein manueller Firmwarewechsel außerhalb dieses Ablaufs wird nicht durch automatisches Umschreiben alter Checkpoints übernommen.

## Sprache und Kommandozeilenoptionen

Vor Setup und Installation von Abhängigkeiten **1 English** oder **2 Deutsch** wählen. Alle ausgewählten Phasen übernehmen die Sprache. Beide Sprachen verwenden dieselben Checkpoints und Backups.

```bash
bash 00_setup.sh --lang en
bash 00_setup.sh --lang de --steps "ALL U"
bash 00_setup.sh --steps 5 --apps "1 2 6"
```

Windows akzeptiert dieselben Optionen:

```powershell
.\00_setup.bat --lang en
.\00_setup.bat --lang de --steps "ALL U"
```

Bei mehreren angeschlossenen USB-Geräten `--serial SERIENNUMMER` ergänzen. Andernfalls wird genau ein autorisierter USB-Stick automatisch erkannt. `--help` zeigt Optionen. `FIRE_TV_LANG=en` oder `FIRE_TV_LANG=de` setzt eine Vorgabe; `--lang` hat Vorrang. Ohne interaktive Eingabe gilt Englisch.

## Kompatibilität

| Fire TV Stick | Modellkennung |
|---|---|
| 4K Max, 2. Generation | `AFTKRT` |
| 4K, 2. Generation | `AFTKM` |
| 4K Plus | `AFTMA08C15` |

Das Gerät muss sich als **`karat`** melden und einer exakten Kombination aus Build, Incremental-Version und Kernel in `SUPPORTED` in [karat.py](karat-automation/karat.py) entsprechen. Eine passende Modellkennung allein genügt nicht. Unbekannte Firmwareprofile bleiben gesperrt.

Manuelles Firmwareupdate und Behebung des Einstellungsfehlers wurden auf einem 4K Plus erfolgreich durchgeführt. Automatische Tests simulieren ADB; sie belegen keine Hardwareprüfung jedes Modells mit jeder Firmware. Sticks der ersten Generation, 4K Select und andere Geräteplattformen gehören nicht zu diesem Ablauf. Ein automatisches Bootrom-/Unbrick- oder Downgrade-Verfahren ist nicht enthalten.

## Entwicklung und gemeldete Gerätedurchläufe

Projekt: [Kuphi/fire-tv-karat-setup](https://github.com/Kuphi/fire-tv-karat-setup/). Dies ist ein unabhängiges, KI-unterstütztes Hobbyprojekt, entwickelt mit ChatGPT-Unterstützung durch Sol- und Astra-Modelle. Eine Unterstützung oder Freigabe durch Amazon, Emotn, OpenAI oder die Upstream-Projekte wird nicht behauptet.

Nach Angaben des Projektautors vom **15. Oktober 2026**:

| Gemeldet von | Gerät | Gerootete Geräte |
|---|---|---|
| Projektautor | Fire TV Stick 4K Max, 2. Generation | 5 |
| Projektautor | Fire TV Stick 4K Plus | 2 |
| Weiterer Tester | Fire TV Stick 4K Plus | 1 |

Bei diesen acht Durchläufen wurden keine dauerhaft unbrauchbar gewordenen Geräte gemeldet. Es handelte sich um Entwicklungsdurchläufe mit verschiedenen Skriptständen, nicht um einen kontrollierten Test jeder Phase der aktuellen Version. Daraus lassen sich weder eine Fehlerquote noch eine Sicherheitsgarantie oder die Prüfung jeder aufgeführten Geräte-/Firmwarekombination ableiten. Der Code enthält Prüfungen und Checkpoints, wurde aber weder professionell sicherheitstechnisch noch rechtlich geprüft. Fehler können Datenverlust oder dauerhafte Geräteschäden verursachen; gesetzliche Rechte und Haftung, die rechtlich nicht ausgeschlossen werden können, bleiben unberührt.

Die zugrunde liegenden Exploit-, Unlock-, Recovery- und Root-Techniken stammen von ihren ursprünglichen Entwicklern, unter anderem den Projekten GhostLock/amonet/TWRP, Magisk, Zygisk Next, Vector, FakeGApps und microG. Dieses Repository koordiniert deren Werkzeuge; es beansprucht nicht, diese Techniken entwickelt zu haben. Upstream-Links stehen in [SOURCES.md](SOURCES.md). Namensnennung ersetzt weder die Einhaltung der jeweiligen Lizenz noch eine gegebenenfalls notwendige Erlaubnis.

## Abhängigkeiten

Das normale Setup benötigt **Python ab 3.10**, **ADB / Android Platform Tools**, eine USB-Datenverbindung, autorisiertes ADB-Debugging, stabile Stromversorgung und Internetzugang für fehlende Downloads. Vor dem Unlock mindestens **12 GiB freien PC-Speicher** bereithalten. Für den normalen Ablauf sind keine pip-Pakete nötig.

### Linux

Fehlendes Python/ADB wird über `tools/install-dependencies.sh` installiert; dafür kann `sudo` erforderlich sein.

| Distribution | Paketmanager | Pakete |
|---|---|---|
| Ubuntu / Debian | `apt-get` | `python3`, `adb`, `curl`, `wget`, `unzip`, `ca-certificates` |
| Fedora | `dnf` | `python3`, `android-tools`, `curl`, `wget`, `unzip`, `ca-certificates` |
| Arch und Derivate | `pacman` | `python`, `android-tools`, `curl`, `wget`, `unzip`, `ca-certificates` |

Bash wird benötigt. Auf älteren Distributionen muss gegebenenfalls separat ein neueres Python installiert werden. Bei `no permissions` die USB-/udev-Regeln prüfen; ADB auf dem PC nicht dauerhaft als Root ausführen, um das Problem zu umgehen.

### Windows

Native BAT-/PowerShell-/Python-Starter sind enthalten; WSL und Git Bash sind nicht erforderlich.

- Fehlendes Python wird über `winget` mit dem Paket für Python 3.13 installiert. Ohne winget Python von [python.org](https://www.python.org/downloads/windows/) installieren und PATH aktivieren.
- Fehlendes ADB wird aus Googles offiziellem Platform-Tools-ZIP nach `tools/platform-tools` geladen.
- Für diesen Download wird vorhandenes `wget.exe` bevorzugt; sonst PowerShell `Invoke-WebRequest`. Der PowerShell-Alias `wget` ist kein GNU wget.
- Einen passenden USB-/ADB-Treiber bei Bedarf separat installieren. Nach der Python-Installation kann ein neues Terminal nötig sein.

Separat verwendete Upstream-amonet-Recovery-Werkzeuge haben eigene Abhängigkeiten. Sie sind für diesen normalen Ablauf nicht nötig; bei eigenständiger Verwendung die Upstream-Anleitung beachten.

## Installationsdateien und Downloads

Das Setup-ZIP enthält Skripte und **fünf Helper-APKs**. Root-ZIPs, Stock-Firmware, Magisk-APK, EmotnUI und Google-APKs werden separat bereitgestellt oder bei Bedarf heruntergeladen.

- [config/required-files.json](config/required-files.json): erwartete Pfade, URLs und vorhandene festgelegte Hashes.
- [config/sources.local.json](config/sources.local.json): enthaltene Standardquellen; Bearbeitung ist optional.
- [SOURCES.md](SOURCES.md): Upstream-Projekte und Quellen.

Passende vorhandene Dateien werden wiederverwendet. Archive, APK-Manifeste und vorhandene festgelegte Hashes werden geprüft. Keinen Hash einer anderen Version einsetzen, um eine abweichende Datei akzeptieren zu lassen.

### packages.zip verwenden

Enthält das Archiv direkt `root`, `google-play` und `emotn`, **nach `packages/` entpacken**. Enthält es bereits einen äußeren Ordner `packages`, diesen stattdessen in den Setup-Ordner entpacken.

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

Die einzelnen Installations-ZIPs nicht entpacken. Eine zusätzliche `Magisk-v30.7.zip` wird nicht verwendet: Das Setup nutzt die vollständige APK und benennt sie bei der Übertragung für die TWRP-Installation um. Für U kann eine vorhandene Firmware-`.bin` in `packages/root/FireOS-8.1.8.2.zip` umbenannt werden; andernfalls wird sie heruntergeladen.

### Wenn ein Download scheitert

Ein fehlgeschlagener oder blockierter Download führt zu einer deutlichen Aufforderung zum manuellen Herunterladen. Sie zeigt Link, exakten Dateinamen und Zielordner. Datei herunterladen, wie angegeben ablegen und **`RESUME`** eingeben. Bei fehlender oder ungültiger Datei bleibt die Abfrage offen; **`EXIT`** beendet ausdrücklich.

Bei Dateien mit festgelegtem Hash können passende Browserdownloads im üblichen `Downloads`-Ordner nach RESUME automatisch geprüft und kopiert werden. Die Originale bleiben erhalten. XDA kann eine Browserbestätigung verlangen. Der Play-Store-Downloader folgt den normalen Downloadschritten der APKMirror-Versionsseite mit frischen Schlüsseln; Serversperren oder abgelaufene Links können dennoch einen manuellen Download erfordern. Dies gilt auch im `--dry-run`.

## Was du am TV erledigen musst

| Abschnitt | Deine Aufgabe |
|---|---|
| Root / Update | Verlangte Bestätigung `ROOT`, `UNLOCK` oder `UPDATE` im Terminal eingeben |
| Magisk | Bei Aufforderung **Install → Direct Install (Recommended)** abschließen; danach `RESUME` im Terminal. Den Neustart übernimmt das Skript |
| Integriertes Zygisk | Normalerweise nichts: Ist es aus, geht Phase 3 automatisch weiter. Ist es an, öffnet das Setup Magisk und verlangt das Ausschalten; danach folgen Prüfung und Neustart |
| FakeGApps | In Vector aktivieren und **ausschließlich System Framework / android** zuordnen |
| microG | In der Selbstprüfung **System spoofs signature** prüfen; Geräteregistrierung und Cloud Messaging selbst aktivieren |
| Emotn | Angeforderte Berechtigungen mit der Fernbedienung erteilen; Anzeige/Navigation prüfen; Launcher-Auswahl bei Aufforderung bestätigen |
| Emotn-Helper | System Clock, Idle Timer und App Categories in Vector aktivieren; **ausschließlich Emotn UI** zuordnen |
| Konten / Stores | Anmeldung und Store-Installationen selbst bestätigen |

Enter allein bestätigt keine Abfrage. Magisks integriertes Zygisk ausgeschaltet lassen; Zygisk Next stellt Zygisk für dieses Setup bereit. Magisk-Preinit und die Vector-SELinux-Regeln werden vor den betreffenden Framework-Neustarts geprüft.

Emotn System Clock folgt der **Zeitzone des Fire TV**, auch nach späteren Änderungen. Es erzwingt weder Berliner Zeit noch eine Gerätezeitzone. Den eigenen Wetterort einstellen; er ist von der Uhr unabhängig. Phase 4 ersetzt bei Bedarf nur den veralteten Helper mit fester Zeitzone.

## Optionale Emotn-Einrichtung: Phase 4

Option **4** weglassen, wenn du EmotnUI nicht möchtest. Beispielsweise `1 2 3 5 U` wählen; das Menü ordnet U trotzdem an der erforderlichen Update-Position ein. App Categories und die anderen Emotn-Helper gehören zu Phase 4 und werden mit ihr übersprungen. Phase 5 kann einen bereits installierten Emotn-Launcher weiterhin optimieren.

Die Vorliebe des Autors für EmotnUI ist persönlich: Auf den verwendeten Geräten bot der Startbildschirm eine werbefreie Oberfläche und Live-Hintergründe. Das ist keine Zusage für zukünftige Drittanbieter-Versionen.

Phase 4 enthält **drei Vector-Module** und **zwei separate Verknüpfungs-Apps**:

| Helper | Typ | Zweck |
|---|---|---|
| Emotn System Clock | Vector-Modul | Der Zeitzone des Fire TV folgen, auch nach Änderungen |
| Emotn Idle Timer | Vector-Modul | Emotns Verhalten bei Inaktivität bzw. beim Bildschirmschoner anpassen |
| Emotn App Categories | Vector-Modul | Gruppierung ausgewählter Apps in Emotn anpassen; dadurch werden sie nicht zu Android-System-Apps |
| FireTV Settings Bridge | Verknüpfungs-App | Zugang zu den Fire-TV-Einstellungen aus dem Launcher bereitstellen |
| Amazon Appstore Direct | Verknüpfungs-App | Alternative Appstore-Verknüpfung anbieten, wenn der vorhandene Emotn-Eintrag nicht funktioniert |

Die drei Vector-Module **ausschließlich Emotn UI** zuordnen. Settings Bridge und Appstore-Verknüpfung sind eigenständige Apps, keine zusätzlichen Vector-Module. Ihr Verhalten hängt von Launcher- und Fire-OS-Version ab.

## Apps in Phase 5 auswählen

| Nummer | App | Bevorzugte Quelle |
|---|---|---|
| 1 | Netflix | Amazon Appstore |
| 2 | YouTube | Amazon Appstore |
| 3 | Prime Video | Amazon Appstore |
| 4 | Disney+ | Amazon Appstore |
| 5 | Wholphin | Offizielle GitHub-APK / Play Store |
| 6 | CX File Explorer | Play Store / passende lokale APK |

`1 2 6`, `ALL`, `NONE` oder `EXIT` eingeben. Bereits installierte ausgewählte Apps werden ohne Neuinstallation optimiert; fehlende ausgewählte Apps zuerst installiert. Nicht ausgewählte Apps werden weder installiert noch optimiert.

Phase 5 setzt immer die Animationswerte auf **0.5** und optimiert Emotn. `NONE` führt ausschließlich diese Aktionen aus. Noch fehlende Apps werden am Ende aufgelistet. Materialious, Aurora, F-Droid und WireGuard werden nicht eingerichtet. **Emotn App Categories gehört zu Phase 4**, nicht ins App-Menü.

## Fortsetzen, Backups und Bereinigung

Nach einer Unterbrechung **dasselbe Hauptskript im selben Ordner** starten. Der gerätegebundene Ablaufplan behält restliche Phasen, App-Auswahl und relevante Optionen. Ausdrückliches `--steps` startet eine neue Auswahl. Ein Phasenfehler sperrt spätere Phasen; unklare Flash-Schreibvorgänge werden niemals automatisch wiederholt.

Beim Ersetzen der Setup-Dateien behalten:

- `karat-automation/runtime/` — Checkpoints, Ablaufpläne und technische Logs;
- `backups/` — geprüfte PC-Backups;
- `packages/` — vorhandene Installationsdateien.

Abgeschlossene geprüfte Unlock-/Backup-Stufen werden wiederverwendet. Alte Windows-Backup-Manifeste mit Backslashes bleiben lesbar; Dateien und Hashes werden weiterhin geprüft. Nur ein eng begrenzt geprüfter historischer Post-OTA-**Vorprüfungsabbruch** kann anhand seines ursprünglichen Logs automatisch wieder aufgenommen werden; ein gestarteter oder nicht nachweisbarer Flash bleibt gesperrt. `pending` nicht von Hand löschen.

| Phase | Bereinigung auf dem Gerät |
|---|---|
| 1 | Keine temporären `/sdcard`-Dateien; laufender temporärer su-Dienst bleibt erhalten |
| 2 | Eigene Magisk-/Post-OTA-Dateien und die beiden eigenen TWRP-Backupordner nach PC-Backup-Prüfung |
| U | Eigene Firmware-/Root-Dateien und das zur Wiederherstellung verwendete Vector-ZIP nach Update-Prüfung |
| 3 | Bekannte Google-/Framework-Dateien sowie APK/APKM-Dateien unter `/sdcard/Download/Downloader` |
| 4–5 | Keine Root-Backup-/Speicherbereinigung |

PC-Backups und fremde TWRP-Backups bleiben erhalten. Eine fehlgeschlagene Phase führt ihre abschließende Bereinigung nicht aus. WLAN wird nach den OTA-Sperrprüfungen aktiviert, sobald Android bereit ist; bei Fehlern erscheint eine Warnung und das Setup geht weiter. In TWRP wird WLAN nicht verändert.

## Bootprobleme

Der bekannte Konflikt betrifft den **Google-Paketverifier**, nicht die Vendor-Partition. Das Setup deaktiviert Googles Verifikations-Receiver nach Installation der Google-APKs, vor der Promotion und vor den betreffenden Android-Neustarts. Es verlangt `new state: disabled` und genau einen aktiven Receiver: `com.amazon.adep/.nimh.receiver.PackageVerificationReceiver`. Das Play-Store-Paket bleibt aktiviert.

Nach sechs Minuten ohne bestätigten Android-Start erscheinen Diagnosehinweise. Ein Timeout allein beweist keinen Verifier-Konflikt. Ungültige `xposed_file`-Labels oder verweigerte `dex2oat`-Ausführung können stattdessen auf fehlende Magisk-Preinit-/Vector-Regeln hindeuten.

USB angeschlossen lassen, Logs und Checkpoints behalten und [MANUAL-REPAIR.md](MANUAL-REPAIR.md) sowie [UPDATE_DE.md](UPDATE_DE.md) beachten. Keine Flash-Vorgänge wiederholen oder Backup-Zustände löschen, um einen Fehler zu umgehen.

## Vorschau und Downloadtest

Für gerätelose Modi muss Python ab 3.10 bereits installiert sein; diese Modi installieren keine Abhängigkeiten.

```bash
# Nur Darstellung: keine Downloads oder Geräteaktionen
bash 00_setup.sh --preview-only --steps "ALL U"

# Echte Downloads und Dateiprüfungen; Geräteaktionen werden simuliert
bash 00_setup.sh --dry-run --steps "ALL U"

# Vorschau der ausgewählten Apps
bash 05_install_apps_and_optimize.sh --preview-only --apps "1 2 6"
```

Unter Windows die passenden `.bat`-Starter mit denselben Optionen verwenden. Ein Downloadtest erstellt lokale Dateien/Logs und kann manuelle Downloads verlangen. Store-Installationen benötigen weiterhin ein Gerät; simulierte Ausgabe ist kein Hardware-Funktionstest.

## Logs, Prüfung und Weitergabe

Die normale Ausgabe zeigt Fortschritt, Status und verlangte Eingaben. Downloads zeigen Datenmenge, Geschwindigkeit und bei bekannter Server-Dateigröße Prozentwerte. Lokale APK-Installationen verwenden eine Aktivitätsanzeige, weil Android keinen Installations-Prozentwert liefert. Vollständige technische Ausgabe steht im angezeigten UTF-8-Log unter `karat-automation/runtime/`. Mit `--verbose` erscheint sie zusätzlich im Terminal; `NO_COLOR=1` deaktiviert Farben.

Offline-Prüfungen umfassen simuliertes ADB-Verhalten, Checkpoints, Update-Reihenfolge und beide Sprachen. Windows-Codepfade werden offline geprüft; native Windows-Ausführung und jede Geräte-/Firmwarekombination wurden nicht auf Hardware getestet. `SHA256SUMS` enthält die Release-Dateihashes. Update-spezifische Prüfgrenzen stehen in [UPDATE_DE.md](UPDATE_DE.md).

Vor Weitergabe oder GitHub-Upload Runtime, Backups, Konten und persönliche Konfiguration ausschließen. Drittanbieter-APKs, Firmware und Helper behalten ihre jeweiligen Lizenz- und Weitergabebedingungen; ihre Nutzung im lokalen Setup erteilt keine Weitergaberechte. Im teilbaren Paket sind kein persönlicher Ort, kein Konto und kein Gerätezustand voreingestellt.
