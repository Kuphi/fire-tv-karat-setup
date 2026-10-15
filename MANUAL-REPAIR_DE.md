# Boot-Logo / Verifier-Konflikt beheben

Zuerst sicherstellen, dass kein Flash mehr läuft. Nur eine Boot-Wartephase abbrechen.
`adb devices -l` muss den richtigen Stick als `device` anzeigen; sonst zuerst die USB-Verbindung klären.
`SERIENNUMMER` in allen Befehlen ersetzen. Befehle einzeln eingeben – sie funktionieren in Bash, fish und PowerShell.

Crash auslesen:
```text
adb -s SERIENNUMMER logcat -b crash -d -t 120
```
`There must be exactly one verifier` mit Amazon und Google belegt den bekannten Konflikt.

1. Gesamtes Promotionsmodul vorübergehend deaktivieren:
```text
adb -s SERIENNUMMER shell "touch /data/adb/modules/microg_installer_revived_again/disable && ls -l /data/adb/modules/microg_installer_revived_again/disable"
```
Nur wenn die Datei angezeigt wird, neu starten:
```text
adb -s SERIENNUMMER reboot
```
2. Nach dem Homescreen Googles Receiver deaktivieren:
```text
adb -s SERIENNUMMER shell pm disable --user 0 com.android.vending/com.google.android.finsky.verifier.impl.PackageVerificationReceiver
adb -s SERIENNUMMER shell cmd package query-receivers --brief --user 0 -a android.intent.action.PACKAGE_NEEDS_VERIFICATION -t application/vnd.android.package-archive
```
Erwartet: `new state: disabled`, exakt ein Receiver von Amazon:
`com.amazon.adep/.nimh.receiver.PackageVerificationReceiver`.

3. Nur bei diesem Ergebnis Modul wieder aktivieren:
```text
adb -s SERIENNUMMER shell "rm /data/adb/modules/microg_installer_revived_again/disable && echo ENABLED"
```
Nur bei `ENABLED`:
```text
adb -s SERIENNUMMER reboot
```
4. Nach zwei Minuten:
```text
adb -s SERIENNUMMER shell getprop sys.boot_completed
adb -s SERIENNUMMER shell cmd package query-receivers --brief --user 0 -a android.intent.action.PACKAGE_NEEDS_VERIFICATION -t application/vnd.android.package-archive
```
Erwartet: `1` und nur Amazon. Dann mit 03_google_play_and_microg und demselben Checkpoint fortsetzen.
Zygisk Next/Vector können nach den Abstürzen deaktiviert sein: in Magisk prüfen, einschalten und bei Bedarf neu starten.
Magisks integriertes Zygisk bleibt ausgeschaltet.

Alternativ bewusst den gleichen Reparaturablauf als Skript starten (Root-ADB und bestehender Checkpoint erforderlich):
Linux:
```text
bash 03_google_play_and_microg.sh --serial SERIENNUMMER --repair-verifier
```
Windows:
```text
03_google_play_and_microg.bat --serial SERIENNUMMER --repair-verifier
```
Dieser Ablauf wiederholt keine Promotion/Flash-Installation und nimmt keine Play-Store-Systemkopie heraus.
Bei unklarem `pending`-Schreibvorgang bleibt die Reparatur gesperrt. Nicht den Checkpoint löschen.
