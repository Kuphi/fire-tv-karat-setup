# Fire TV karat – zweisprachiges Setup-Paket

[English](README.md) · [Deutsch](README_DE.md)

## Sprache wählen

Unter Windows `00_setup.bat`, unter Linux `bash 00_setup.sh` verwenden. Vor dem Setup oder der Installation von Abhängigkeiten **1 English** oder **2 Deutsch** wählen. Alle ausgewählten Phasen übernehmen diese Sprache. Die einzelnen Phasenstarter und Python-Einstiege bieten dieselbe Auswahl.

Mit `--lang en` oder `--lang de` wird die Abfrage übersprungen. Ohne interaktive Eingabe gilt Englisch. `FIRE_TV_LANG=en` oder `FIRE_TV_LANG=de` legt ebenfalls die Sprache fest; ein ausdrückliches `--lang` hat Vorrang.

```bash
bash 00_setup.sh --lang de
bash 00_setup.sh --lang en --preview-only --steps ALL
```

Windows:
```text
00_setup.bat --lang de
00_setup.bat --lang en
```

Beide Sprachen verwenden dieselbe Engine, Checkpoints, Backups und Ablaufpläne. Ein Sprachwechsel startet abgeschlossene Arbeiten nicht erneut. Beim Aktualisieren Runtime, PC-Backups und Packages behalten. Alte deutsche Logs bleiben für die Wiederaufnahme lesbar. Die Standarddokumentation ist `README.md`; diese deutsche Anleitung heißt `README_DE.md`.


Stand: 2026-10-14. Enthält Skripte und fünf mitgelieferte Helper-APKs.
Keine persönlichen Logs, Checkpoints, Seriennummern, Backups, Konten oder VPN-Konfigurationen sind enthalten.

## Optionales Firmwareupdate: U

Die Optionen **1–5** bleiben erhalten. **ALL U** ergänzt Fire OS **8.1.8.2**: Das Update wird vor Google/microG in Phase 2 integriert. Firmware, Post-OTA und Magisk werden in einer TWRP-Sitzung geflasht. **U** funktioniert auch allein. Zuvor aktive Vector-/microG-Module werden erst nach Preinit- und Verifier-Prüfungen wiederhergestellt. Zum Fortsetzen einfach dasselbe Hauptmenü starten.

Ablauf, Checkpoints, Firmware-Hash und Prüfgrenzen stehen in [UPDATE_DE.md](UPDATE_DE.md). Vorschau: `bash 00_setup.sh --lang de --preview-only --steps "ALL U"` (Windows: `00_setup.bat` mit denselben Optionen).

## Hauptmenü und Reihenfolge

Linux: `bash 00_setup.sh` · Windows: `00_setup.bat`.
Im Menü z.B. **1,2,3**, **3,4,5** oder **ALL** wählen. Die Auswahl wird dedupliziert und sortiert.
Das Menü bindet die tatsächlichen Phasen an denselben USB-Stick. Bei einem Fehler startet es keine weitere Phase.

| Phase | Linux-Starter | Aufgabe |
|---|---|---|
| 00 | `00_setup.sh` | Hauptmenü / Auswahl |
| 01 | `01_temporary_root_and_disable_ota.sh` | temporäres Root und OTA-Sperre |
| 02 | `02_permanent_root_magisk.sh` | Unlock, einmaliges Backup, Post-OTA, Magisk |
| 03 | `03_google_play_and_microg.sh` | Google Play, microG, Zygisk Next, Vector, FakeGApps |
| 04 | `04_emotn-launcher-setup.sh` | Emotn Launcher |
| 05 | `05_install_apps_and_optimize.sh` | Apps installieren und optimieren |

Zu jedem Starter gibt es eine native Windows-`.ps1` und `.bat` mit gleichem Namen.
Auch die Phasenstarter können direkt aufgerufen werden.

```bash
bash 00_setup.sh --steps 1,2,3 --dry-run
bash 00_setup.sh --steps ALL --preview-only
bash 03_google_play_and_microg.sh --dry-run
```

01 verlangt `ROOT` als Bestätigung, wenn temporäres Root hergestellt werden muss.
Es entsperrt keinen Bootloader und macht kein Backup. OTA und OTA-Override werden deaktiviert und geprüft.
Temporäres Root geht bei Neustart verloren; deshalb wird es nicht als dauerhaft erledigt übersprungen.
02 kann bei Bedarf temporäres Root selbst herstellen und verlangt vor Unlock weiterhin `UNLOCK`.
03 benötigt bereits permanentes Root mit Magisk 30.7; 04 benötigt das eingerichtete Framework/Vector.
Einmaliges Backup und vorhandene Flash-Checkpoints bleiben erhalten; kein zweites Backup beim Google-Schritt.

Immer das vollständige Paket entpacken. Die Starter finden ihren Hauptordner auch aus einem anderen Arbeitsverzeichnis.
Bei genau einem autorisierten USB-Gerät wird dessen Seriennummer automatisch erkannt.
Bei mehreren Geräten: `--serial SERIENNUMMER` ergänzen; PowerShell/BAT verwenden dieselben Optionen.
Mit `--help` zeigt jeder Python-Einstieg seine Optionen. `--prepare-only` gibt es für die Root-Phasen und Emotn (Dateien prüfen/herunterladen, keine Geräteänderungen).
Checkpoint-Dateien und Logs entstehen erst bei Benutzung in `karat-automation/runtime`; beim Weitergeben NICHT mitpacken.

## Abhängigkeiten und Installation

Python **>=3.10** (nur Standardbibliothek; kein pip für den normalen Ablauf), Android Platform Tools/ADB,
USB-Datenkabel und autorisiertes USB-Debugging, stabile Stromversorgung, Internet für fehlende Downloads.
Vor dem Unlock mindestens 12 GiB freien PC-Speicher für die Backups vorsehen.
Linux braucht Bash; Windows verwendet native Python-/PowerShell-/BAT-Starter, kein WSL oder Git Bash nötig.

Die Linux-Starter installieren fehlendes Python/ADB über `tools/install-dependencies.sh`:

| Distribution | Paketmanager | Pakete |
|---|---|---|
| Ubuntu / Debian | apt-get | python3, adb, curl, wget, unzip, ca-certificates |
| Fedora | dnf | python3, android-tools, curl, wget, unzip, ca-certificates |
| Arch / darauf basierende Distributionen | pacman | python, android-tools, curl, wget, unzip, ca-certificates |

Dazu kann sudo erforderlich sein. Sehr alte Distributionen mit Python <3.10 benötigen ein neueres Python.
Bei `no permissions` Linux-USB-/udev-Regeln der Distribution prüfen; ADB nicht blind dauerhaft als root starten.

Windows: Python 3.13 wird bei Bedarf über winget installiert. Falls winget fehlt, Python selbst von python.org
installieren (PATH aktivieren). ADB wird aus Googles offizieller Platform-Tools-ZIP unter `tools/platform-tools` entpackt.
Zum Download wird vorhandenes **wget.exe** bevorzugt; sonst PowerShell `Invoke-WebRequest`.
Der PowerShell-Alias `wget` ist kein GNU wget und wird nicht dafür verwendet.
Ein passender USB-/ADB-Treiber ist bei Bedarf separat erforderlich; das Skript installiert keine beliebigen Treiber.
Nach erstmaliger Python-Installation kann ein neues Terminal nötig sein.
Native Windows-Hardwaretests wurden hier nicht ausgeführt; die plattformspezifischen Codepfade wurden offline geprüft.

Optionale externe Recovery-Werkzeuge aus amonet sind NICHT Bestandteil des normalen Ablaufs.
Deren Python-Abhängigkeiten (u.a. pyserial, pycryptodome, PyYAML, future, iso8601) gelten nur bei separater Nutzung
und müssen nach den jeweiligen Upstream-Anweisungen installiert werden. Keine alten requirements global installieren.

## Geräte und Firmware

| Modell | Kennung | Status dieses Pakets |
|---|---|---|
| Fire TV Stick 4K Max (2nd Gen) | AFTKRT | bisheriger Ablauf, mit Offline-Regressionstests |
| Fire TV Stick 4K (2nd Gen) | AFTKM | Gerätekennung ergänzt; keine eigenen Hardwaretests |
| Fire TV Stick 4K Plus (2025) | AFTMA08C15 | Gerätekennung ergänzt; keine eigenen Hardwaretests |

TWRP-Upstream nennt alle drei als karat/MT8696-Geräte. Die Erkennung akzeptiert ausschließlich `karat`,
diese drei Modellkennungen und die EXAKTEN Build-/Incremental-/Kernel-Kombinationen in `SUPPORTED` in `karat.py`.
Die vorhandenen 15 Firmwareprofile wurden nicht um unbestätigte Builds erweitert. Die GhostLock-Dokumentation
beschreibt den karat-Target als 4K Max; die Freigabe aller Modellkennungen ist deshalb kein Beleg für
hardwaregetestete Root-Unterstützung jeder Firmware auf jedem Modell. Ein unbekanntes Profil bleibt gesperrt.
4K Select, erste Generation, andere SoCs und Android-/Vega-Varianten sind NICHT freigegeben.
Kein Downgrade, keine automatischen Bootrom-/Unbrick-Versuche.

## Benötigte externe Installationsdateien

Im Upload fehlten die Root-ZIPs, EmotnUI und mehrere Drittanbieter-APKs. Sie sind deshalb nicht in diesem ZIP enthalten.
`config/required-files.json` listet Pfade, Versionen, gepinnte SHA256 und vorhandene Download-URLs.
Die drei Root-ZIPs und EmotnUI haben jetzt die bereitgestellten Download-URLs. Bekannte HTTPS-URLs werden von den jeweiligen Phasen automatisch verwendet; nach dem Download werden Archiv, Manifest und vorhandene gepinnte SHA256 geprüft. Die neuen URLs konnten hier nicht durch einen tatsächlichen Download verifiziert werden. Fehlende Dateien ohne URL selbst bereitstellen;
Die echte `config/sources.local.json` ist bereits enthalten. Sie enthält dieselben verfügbaren Standardlinks wie `FILES`; Änderungen sind optional. Die Example-Datei dient nur als Vorlage.
Gepinnte Hashwerte dürfen nicht mit anderen Versionen überschrieben werden.

Benötigte Dateien (Root-ZIPs/EmotnUI werden bei Bedarf über die eingetragenen Links heruntergeladen):
- `packages/root/amonet-karat-v1.3.0.zip`
- `packages/root/ghostlock-karat-v1.0.4.zip`
- `packages/root/post-ota-karat-v1.0.0.zip`
- `packages/emotn/EmotnUI.apk`
- `packages/google-play/play-store-tv.apk` (TV-Variante `com.android.vending`, Version 52.0.20-24): APKMirror-Seite aus `config/required-files.json` im Browser öffnen und die APK hier ablegen. Als Standard ist die dauerhafte APKMirror-Versionsseite hinterlegt. Der Downloader löst die öffentlichen Downloadknöpfe mit frischen Schlüsseln, einer normalen Cookie-Sitzung und den passenden Referer-Angaben auf. Keine alten Downloadschlüssel werden gespeichert. Die fertige APK wird per SHA256 und Manifest geprüft.

Magisk 30.7, Zygisk Next 1.5.0, Vector 2.2, FakeGApps 6.6, microG 0.3.15.250932,
microG Installer Revived Again 1.1.2 haben Downloadquellen im Skript.
Die Root-ZIPs wurden nicht aus fremden APK-/ZIP-Portalen nachbeschafft.

## Ablauf und Bestätigungen

02 fordert `UNLOCK` vor dem Root-/Unlock-Versuch. GhostLock versucht maximal zweimal temporäres Root,
jeweils nach geprüftem Neustart. Bootloader-/IDME-/Flash-Schreibvorgänge werden niemals automatisch wiederholt.
Root kann das Gerät dauerhaft unbrauchbar machen; die späteren Backups schützen nicht vor einem misslungenen Unlock.
USB/Strom während der Schreibvorgänge angeschlossen lassen.

Die vollständige Magisk-App wird lokal installiert und ihr installierter APK-Hash geprüft.
Nach Abschluss von Direct Install im Terminal `RESUME` eingeben. Das Skript startet den Stick neu, wartet auf Android, prüft Root, Magisk 30.7 und die vollständige App und räumt danach auf. Der Reboot-Knopf in Magisk wird nicht benötigt. Auch bei älteren abgeschlossenen Phase-2-Checkpoints holt das Hauptskript diesen Neustart nach.
Bei Bedarf folgt ein lokaler Reparaturversuch, danach eine manuelle WLAN-Installation von derselben v30.7-APK.
`RESUME` setzt fort, `EXIT` beendet die Abfrage; Enter allein bestätigt nichts.
In Magisk integriertes Zygisk AUS, Zygisk Next und Vector aktiv. FakeGApps ausschließlich System Framework/android zuordnen.
microG Self-Check prüfen; Geräteregistrierung und Cloud Messaging selbst aktivieren. Konten selbst einrichten.

### Verifier-Konflikt und Boot-Timeout

Es geht um den **Google-Paketverifier**, nicht um die Vendor-Partition:
`com.android.vending/com.google.android.finsky.verifier.impl.PackageVerificationReceiver`.
Das Skript deaktiviert ihn unmittelbar nach der Google-APK-Installation, vor Promotion und direkt vor dem microG-Reboot.
Die Ausgabe muss mit `new state: disabled` enden; exakt ein Receiver muss übrig bleiben:
`com.amazon.adep/.nimh.receiver.PackageVerificationReceiver`.
Der Play Store bleibt aktiviert und seine Promotion bleibt erhalten. Nach dem Boot wird erneut geprüft.

Das vermindert den bekannten Konflikt, garantiert aber keinen fehlerfreien Boot: der Zustand kann sich beim Paket-Scan ändern,
und andere Bootfehler sind möglich. Nach sechs Minuten ohne bestätigten Start erscheint eine Reparaturanleitung,
kein automatischer weiterer Flash. Siehe `MANUAL-REPAIR_DE.md`.

### Bereinigung nach den drei Root-Phasen

- 01 legt keine temporären Dateien auf `/sdcard` ab. GhostLock-Dateien liegen unter `/data/local/tmp`; der noch laufende su-Daemon wird nicht gelöscht.
- 02 entfernt Magisk-/Post-OTA-ZIPs auf `/sdcard` sowie beide eigenen TWRP-Gerätebackups erst nach Prüfung der PC-Kopien und ihrer SHA256. Fremde Backups und PC-Dateien bleiben erhalten.
- 03 entfernt die bekannten Google-/Framework-Staging-Dateien und APK/APKM-Dateien unter `/sdcard/Download/Downloader`. Das Backup wird nicht erneut erstellt oder gelöscht.
- Leere Verzeichnisse werden entfernt; keine pauschale Löschung fremder TWRP-Backups.
- 04/05 enthalten keine solche Speicherbereinigung.

Bei übernommenen Root-Installationen ohne verifizierte PC-Backups bleibt die Backup-Löschung gesperrt.
Wenn eine Phase scheitert, wird ihre abschließende Bereinigung nicht ausgeführt.

### Emotn und Apps

04: Emotn installieren, Home-Zuordnung und Vector-Module nach Anleitung bestätigen.
Als Wetterstadt **den eigenen Wohnort** einstellen. Emotn System Clock folgt der Fire-TV-Zeitzone und reagiert auf Änderungen. Wetterstadt und Gerätezeitzone werden nicht verändert. Keine persönlichen Städte oder Konten sind voreingestellt.

05: Animationen 0.5; vorhandene Apps überspringen, fehlende installieren, danach `compile -m speed -f`.
Netflix, YouTube, Prime Video und Disney+ werden bevorzugt im Amazon Appstore geöffnet.
Wholphin wird nach Möglichkeit direkt aus dem offiziellen GitHub-Release installiert.
CX verwendet eine passende lokale APK oder den Play Store. Materialious, Aurora, F-Droid und WireGuard werden überhaupt nicht eingerichtet.
Store-Installationen selbst bestätigen, dann `RESUME`; fehlende Apps werden abschließend gemeldet.
Emotn App Categories wird in Phase 4 mit den Launcher-Helfern installiert. In Vector aktivieren und ausschließlich Emotn UI zuordnen. Phase 5 enthält sechs Apps zur Auswahl. Der Launcher wird am Ende neu gestartet.

## Prüfen und Weitergeben

`python3 -m unittest discover -s karat-automation -p 'test_*.py' -v` (Windows: `py -3 -m unittest ...`).
`SHA256SUMS` enthält die Prüfsummen des fertigen Pakets.
Tests sind Offline-Tests mit Mock-ADB; keine echten USB-, Windows-, Flash- oder Geräteprüfungen.
Nach Benutzung Runtime, Backups, persönliche sources.local.json und Kontodaten nicht weitergeben.
Die fünf Helper-APKs stammen aus dem bereitgestellten Paket; ihre Hashes wurden geprüft.
Drittanbieter-Downloads und eigene Helper unterliegen ihren jeweiligen Nutzungs-/Weitergabebedingungen.

Quellen: siehe `SOURCES_DE.md`. Keine erfundene Erfolgsgarantie für Root oder Boot.

## Download-Dry-Run ohne angeschlossenen Stick

`--dry-run` lädt benötigte Dateien tatsächlich herunter, prüft Archive/Manifeste/Hashes und zeigt danach die simulierte Geräteausgabe.
Vorhandene geprüfte Dateien werden wiederverwendet. Downloads und Logs werden lokal gespeichert; kein ADB und keine Geräteänderungen.
Die Standardlinks stehen in `FILES` in `karat-automation/karat.py`; eine eigene sources.local.json ist dafür NICHT erforderlich.
Leere URL-Einträge in älteren Konfigurationen überschreiben die Standardlinks nicht mehr.
Bei HTTP-Fehlern nennt die Meldung jetzt die betroffene Datei.

```bash
bash 02_permanent_root_magisk.sh --dry-run
bash 04_emotn-launcher-setup.sh --dry-run
bash 05_install_apps_and_optimize.sh --dry-run
```

Für die reine Optik ohne Downloads/Dateien:
```bash
bash 02_permanent_root_magisk.sh --preview-only
bash 04_emotn-launcher-setup.sh --preview-only
bash 05_install_apps_and_optimize.sh --preview-only
bash 02_permanent_root_magisk.sh --preview-only --dry-run-scenario boot-timeout
```
Windows: entsprechende `.bat`-Starter mit denselben Optionen verwenden. Python >=3.10 muss für diese gerätefreien Modi bereits installiert sein.
Store-Installationen können ohne Gerät nicht durchgeführt werden; App-Dry-Run meldet sie als fehlend.
Alle Geräteergebnisse sind simuliert, keine echte Funktionsprüfung. Download-URLs können serverseitig ablaufen oder blockiert werden.

## Wenn ein Download nicht automatisch klappt

HTTP 403/404, abgelaufene Links oder HTML statt APK führen jetzt zu einer gut sichtbaren manuellen Download-Abfrage.
Das Skript zeigt Link, Dateiname und den absoluten Ablageordner in vier einfachen Schritten.
Die Datei passend ablegen, ZIP nicht entpacken, dann `RESUME` schreiben. Die Datei wird erneut geprüft.
Eine fehlende/falsche Datei hält die Abfrage offen. `EXIT` beendet ausdrücklich; ohne interaktive Eingabe wird eine Wiederaufnahmeanleitung ausgegeben.
Das gilt auch beim Download-Dry-Run. Es werden keine Schutzmechanismen der Downloadseiten umgangen.
Der Play Store wird manuell auf dieser Seite angeboten:
https://www.apkmirror.com/apk/google-inc/google-play-store-android-tv/google-play-store-android-tv-52-0-20-release/google-play-store-android-tv-52-0-20-24-8-pr-937697325-4-android-apk-download/

### Browser-Fallback bei XDA

Eine direkte HTTP-Anfrage an XDA wurde mit `403` und `cdn-challenge: true` beantwortet: die Seite verlangt eine Browser-Bestätigung. Das betrifft auch curl; ein vollständig unbeaufsichtigter Download ist dann nicht verfügbar.
Das Skript öffnet im interaktiven Terminal den Link im normalen Browser. Dort die Bestätigung durchführen und die ZIP herunterladen.
Im normalen `~/Downloads`-Ordner speichern und `RESUME` eingeben: Die exakt benannte Datei (auch mit Browser-Suffix `(1)` etc.) wird nur bei passender gepinnter SHA256 automatisch in den Paketordner kopiert.
Unpassende Dateien bleiben unberührt; die originale heruntergeladene Datei wird nicht gelöscht. Bei abweichendem Downloadordner weiterhin den explizit angezeigten Zielpfad verwenden.
Es werden keine Challenge-Cookies exportiert und keine Anti-Bot-Sperren umgangen. Für vollständig offline verfügbare Root-Dateien können die drei Original-ZIPs vorab unter `packages/root` abgelegt werden.

### Verifizierter Play-Store-Direktdownload (2026-10-13)

Die APKMirror-Versionsseite wird ohne Browser über ihre regulären Downloadstufen aufgelöst.
Ein Live-Download ergab 66.201.277 Bytes und SHA256
`16625b025c342c3badb63c60ba4158291863d21fa8bb7e6b16899144ab6037b6`.
Das APK-Manifest wurde als `com.android.vending`, VersionCode `85202008` bestätigt.
Die Datei ist hier nur zur Verifikation heruntergeladen worden; sie wird nicht im Share-ZIP mitverteilt.
XDA-Root-ZIPs haben weiterhin eine Browser-Challenge. Es wurde keine alternative freigegebene Direktquelle für dieselben Dateien gefunden. Diese Downloads sind nicht als repariert bestätigt.

## Separates packages.zip verwenden

Das Skriptpaket enthält weiterhin nur die Skripte und Helper. Das zusätzlich angebotene `packages.zip` separat herunterladen und **dessen Inhalt in den Ordner `packages` entpacken**.
Am Ende muss die Struktur so aussehen:

```text
fire-tv-karat-setup/
  00_setup.sh (bzw. .bat)
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
    emotn/helpers/ (die fünf Helper-APKs)
```

Linux im Hauptordner:
```bash
mkdir -p packages
unzip -n packages.zip -d packages
```
Windows PowerShell im Hauptordner:
```powershell
Expand-Archive -LiteralPath .\packages.zip -DestinationPath .\packages
```

Diese Befehle setzen voraus, dass `packages.zip` direkt `root`, `google-play` und `emotn` enthält. Falls das ZIP bereits einen äußeren Ordner `packages` enthält, diesen direkt in den Hauptordner entpacken. **Kein `packages/packages/root` erzeugen.**
Vorhandene Dateien haben Vorrang vor Web-Downloads. Archive, Versionen und gepinnte SHA256 werden trotzdem geprüft.
Die optional vorhandene `Magisk-v30.7.zip` bleibt unbenutzt: das Skript verwendet die vollständige APK und benennt sie nur beim Transfer fürs Flashen um.

## App-Auswahl in Phase 05

```bash
bash 05_install_apps_and_optimize.sh
```

Im Menü z.B. **1 2 6** eingeben:

| Nummer | App | Quelle |
|---|---|---|
| 1 | Netflix | Amazon Appstore |
| 2 | YouTube | Amazon Appstore |
| 3 | Prime Video | Amazon Appstore |
| 4 | Disney+ | Amazon Appstore |
| 5 | Wholphin | offizielle GitHub-APK / Play Store |
| 6 | CX File Explorer | Play Store / passende lokale APK |

`ALL` wählt alle, `NONE` nur die Animationseinstellungen/Emotn-Optimierung, `EXIT` beendet ohne Einrichtung.
Nicht ausgewählte Apps werden weder installiert noch optimiert. Bereits installierte ausgewählte Apps werden nur optimiert.
Die Animationseinstellungen und Emotn-Optimierung bleiben Bestandteil von Phase 05.

Direkt oder über das Hauptmenü:
```bash
bash 05_install_apps_and_optimize.sh --apps "1 2 6"
bash 00_setup.sh --steps 5 --apps "1 2 6"
bash 05_install_apps_and_optimize.sh --preview-only --apps "1 2 6"
```
Windows: entsprechende `.bat`-Starter mit denselben Optionen.
Materialious, Aurora, F-Droid und WireGuard sind aus allen Einrichtungs-/Downloadlisten entfernt. `--extras` wurde entfernt; vorhandene Installationen dieser Apps werden nicht angefasst.

## Übersichtliche Terminalausgabe

Standardmäßig erscheinen nur Fortschritt, geprüfte Dateien, Installationsstatus, Warnungen und notwendige Eingaben.
Ausführliche ADB-/aapt-Ausgaben, komplette SHA256 und Hostdetails stehen weiterhin im UTF-8-Detailprotokoll unter `karat-automation/runtime`.
Der Logpfad wird angezeigt. Mit `--verbose` werden alle Details zusätzlich im Terminal ausgegeben:
```bash
bash 00_setup.sh --verbose
bash 03_google_play_and_microg.sh --verbose
```

Farben werden automatisch nur in einem geeigneten interaktiven Terminal aktiviert; bei Umleitung bleibt die Ausgabe ohne ANSI-Steuerzeichen.
Mit der Umgebungsvariable `NO_COLOR=1` lassen sich Farben abschalten. Windows-Starter bieten dieselben Optionen.
Eingabefelder zeigen deutlich die erlaubten Begriffe: `ROOT`, `UNLOCK`, `RESUME`, `EXIT` beziehungsweise die Nummern im Menü.
Leere oder falsche Bestätigungen starten keine Schritte und halten die Abfrage offen.
`--dry-run` und `--preview-only` zeigen im interaktiven Terminal ebenfalls die Auswahl; per `--steps`/`--apps` lässt sie sich direkt vorgeben.

## Automatische Wiederaufnahme über das Hauptskript

Zum Fortsetzen einfach wieder das Hauptskript verwenden: Windows `00_setup.bat`, Linux `bash 00_setup.sh`.
Es erkennt den angeschlossenen USB-Stick und speichert die gewählte Phasenfolge pro Stick in `karat-automation/runtime`. Nach einem Abbruch setzt es mit den noch offenen Phasen fort. App-Auswahl und relevante Ablaufoptionen bleiben erhalten. Abgeschlossene Unlock-/Backup-Schritte werden nicht wiederholt. Mit ausdrücklich angegebenem `--steps` kann eine neue Auswahl getroffen werden.

Für einen alten Checkpoint mit `pending=postota` oder einem anderen offenen permanenten Root-Schritt erkennt das Hauptskript Phase 2 automatisch. Da alte Versionen die Menüauswahl noch nicht speicherten, werden weitere Phasen nicht erfunden oder automatisch hinzugefügt. Bei künftig gespeicherten Abläufen bleibt die komplette ursprünglich gewählte Restfolge erhalten.

Die neue Version setzt `pending=postota` erst unmittelbar vor dem tatsächlichen `twrp install`, nach Backupprüfung, Byteprüfung und geprüftem Transfer. Eine gescheiterte Vorprüfung erzeugt damit keinen unklaren Flash-Checkpoint mehr.

Ein altes `pending=postota` kann aus einem vollständigen, zum selben Stick gehörenden Vorprüfungs-Abbruchlog der bekannten deutschen Version vom 2026-10-13 16:06:40 wieder aufgenommen werden. Das Hauptskript sucht dieses frühere Log automatisch im Runtime-Ordner. Es muss ein ausdrücklicher Abbruch protokolliert sein, ohne gestarteten Installationsbefehl. TWRP und PC-Backups werden geprüft; vor dem Zurücksetzen wird der Checkpoint gesichert. Post-OTA wird nicht als erledigt markiert: seine Vorprüfungen laufen erneut. Ein unverändert falscher Bytecheck muss weiterhin untersucht werden.

Ein tatsächlich gestarteter Flash, fehlende/abgeschnittene Logs oder unbekannte Skriptversionen werden nicht automatisch wiederholt. Ein Diagnose-Log mit abgeschlossenen Backups allein beweist keinen erfolgreichen Post-OTA-Schritt. Die Ausgabe nennt nach Möglichkeit das frühere Fehlerlog und den ursprünglichen Fehler. `Pending` nicht von Hand löschen.

Neue Dateien über die vorhandene Installation entpacken; `karat-automation/runtime`, PC-Backups und `packages` behalten. Bei mehreren Geräten `--serial SERIENNUMMER` ergänzen. Die Wiederaufnahme garantiert keinen erfolgreichen Post-OTA-Flash bei einem bislang unbekannten ursprünglichen Fehler.

## Windows-Backup-Pfade

Ältere Windows-Versionen speicherten relative Pfade in `verified.json` mit Backslashes. Die Prüfung auf vollständige Boot-/Data-/System-Backups erwartete dagegen Schrägstriche. Diese Version akzeptiert beide Schreibweisen und schreibt neue relative Backup-Pfade mit `/`. Vorhandene Manifeste werden nicht überschrieben; Dateien und ihre SHA256 werden weiterhin geprüft. Ein wirklich fehlendes oder verändertes Backup bleibt gesperrt.

Die Fortsetzung erfolgt wie gewohnt über `00_setup.bat` beziehungsweise `bash 00_setup.sh`. Runtime, vorhandene PC-Backups und Packages beim Aktualisieren behalten.

## Uhr folgt der Fire-TV-Zeitzone

Phase 04 installiert nun `Emotn-System-Clock.apk` statt der festen Berlin-Uhr. Der Helper liest `persist.sys.timezone` bei jeder Zeitzonenabfrage, reagiert auf Android-Zeitzonenänderungen und aktualisiert den Launcher im Vordergrund beziehungsweise bei der Rückkehr aus dem Hintergrund. Ist die Eigenschaft nicht verfügbar, wird die aktuelle Android-Standardzeitzone verwendet. Die Gerätezeitzone wird weder verändert noch vorgeschrieben. Die Wetterstadt bleibt unabhängig.

Das neue Paket heißt `local.karat.emotnsystemclock`. Phase 04 entfernt ausschließlich den alten Helper `local.karat.emotnclock` und installiert den Ersatz. In Vector **Emotn System Clock** aktivieren und ausschließlich **Emotn UI** zuordnen. Ein neuer Scope-Checkpoint zeigt diese Abfrage auch beim Aktualisieren bestehender Installationen. Der Launcher wird zum Anwenden einmal neu gestartet; spätere Zeitzonenänderungen benötigen keinen erneuten Setup-Lauf.

Die aktualisierte Uhr-APK ist direkt enthalten; für die Installation werden weder ein Helper-Quellcodeordner noch Bauwerkzeuge benötigt. Sie ist für Emotn UI 1.1.0.2 ausgelegt. APK-Signaturen und Offline-Verhalten wurden geprüft; ein Test auf einem echten Fire TV steht aus.

## GhostLock: Auf betriebsbereiten Root-Dienst warten

Die `ROOTED`-Markierung kann erscheinen, bevor su-Client und Root-Daemon bereit sind. Das Setup wartet nun auf ein tatsächliches `uid=0` und prüft sowohl `su` als auch `/data/local/tmp/su`. Ein noch fehlender Client (Exit 127) führt nicht sofort zum Abbruch. Für temporäre OTA-/Unlock-Befehle wird anschließend der geprüfte Client verwendet.

Das Hauptskript kann `pending=ghostlock` fortsetzen. Zuerst wird ein vorhandener Root-Dienst geprüft. Ist er nicht verfügbar, verwirft ein geprüfter Neustart den temporären Versuch vor dem noch erlaubten Wiederholungsversuch. Das Limit von zwei Versuchen bleibt auch über Neustarts erhalten. Andere offene Schreibvorgänge werden nicht zurückgesetzt. Runtime, Backups und Packages beim Aktualisieren behalten; wie gewohnt `00_setup.bat` oder `bash 00_setup.sh` verwenden.

Downloads zeigen einen Fortschrittsbalken mit Datenmenge, Prozentwert bei bekannter Dateigröße, Geschwindigkeit und vergangener Zeit. Ohne Größenangabe wird die empfangene Datenmenge angezeigt. Lokale APK-Installationen zeigen einen animierten Aktivitätsbalken bis ADB fertig ist; Android liefert keinen Installations-Prozentwert. Store-Downloads sind auf dem Fernseher sichtbar. Vor der microG-Selbstprüfung öffnet das Skript die microG-Einstellungen automatisch; dort Selbstprüfung wählen.

WLAN wird am Ende von Phase 1 wieder aktiviert, sobald beide OTA-Update-Pakete als deaktiviert bestätigt sind. Phase 2 prüft diese erneut und aktiviert WLAN, wenn Android nach Post-OTA wieder gestartet ist, auch bei Wiederaufnahme. In TWRP wird WLAN nicht verändert. Falls die Aktivierung scheitert, erscheint eine deutliche Warnung und die Einrichtung geht weiter; die Verbindung nutzt die bereits auf dem Stick gespeicherten Netzwerkeinstellungen.

Phase 3 prüft Magisks integriertes Zygisk automatisch. Ist es ausgeschaltet (Standard auf echten Geräten), geht es ohne Öffnen von Magisk oder RESUME-Abfrage weiter. Nur bei aktivierter Einstellung öffnet das Skript Magisk, fordert zum Deaktivieren auf, prüft erneut und startet vor der Framework-Installation neu.
