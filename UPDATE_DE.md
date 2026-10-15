# Optionales Fire-OS-Update

[English](UPDATE.md) · [Hauptanleitung](README_DE.md)

Wie gewohnt `bash 00_setup.sh` unter Linux oder `00_setup.bat` unter Windows starten.

| Auswahl | Ergebnis |
|---|---|
| `ALL` | Phasen 1–5 ohne Firmwareupdate |
| `ALL U` | Phase 1, kombinierte Phase 2 mit Update, danach Phasen 3–5 |
| `2 U` | Permanentes Root und Update in einer TWRP-Sitzung |
| `U` | Bestehende Installation aktualisieren; Unlock und Backup bei Bedarf nachholen |
| `U 3 4` | Update, danach Google/microG und Emotn |

U installiert ausschließlich **8.1.8.2 / RS8182.3811N / 0032548774788** auf geprüften karat-Geräten. Die genauen Modell-, Firmware- und Kernelprüfungen bleiben aktiv. Neuere Firmware wird nicht heruntergestuft; bereits installiertes 8.1.8.2 und abgeschlossene Update-Vorgänge werden nicht erneut geflasht.

## Reihenfolge

1. Firmware mit Fortschritt herunterladen, festgelegten SHA-256 und ZIP-Integrität prüfen. Passende vorhandene Dateien wiederverwenden.
2. Identität prüfen, `UPDATE` bestätigen; ein neuer Unlock benötigt zusätzlich `UNLOCK`. Das durch dieses Setup installierte Amonet-karat-TWRP **3.7.1_12-0** verwenden. Die gleiche Versionsanzeige einer fremden Recovery beweist nicht dieselben Partitionsschutzfunktionen.
3. Geprüftes PC-Backup wiederverwenden oder einmalig erstellen. Backups nicht überschreiben. Nach Prüfung der PC-Kopien nur die eigenen Geräte-Backupordner entfernen, um Platz freizugeben.
4. Vor Verlassen von Android bei vorhandenem Play Store Google-Verifier deaktivieren; ausschließlich Amazons Receiver verlangen. In TWRP den Aktivierungszustand von Vector und microG-Promotion speichern, dann beide deaktivieren. Bereits deaktivierte Module bleiben deaktiviert. Ausstehende Modulinstallationen blockieren das Update.
5. **Eine TWRP-Sitzung:** Firmware flashen, drei bekannte adbd-Byteprüfungen ausführen, Post-OTA und Magisk installieren. Kein Android-Start dazwischen. Fehlgeschlagene Prüfungen verhindern weitere Flash-Vorgänge.
6. Android starten, exakte Zielfirmware samt Kernel und Magisk 30.7 prüfen. WLAN erst nach bestätigter OTA-Sperre aktivieren. Vollständige lokale Magisk-App installieren und per Hash prüfen.
7. Am TV **Magisk → Install → Direct Install (Recommended)** ausführen, danach im Terminal `RESUME` eingeben. Das Skript startet neu und prüft beschreibbaren Preinit-Speicher. Fehlt er, fordert es erneut Direct Install an und prüft nach einem weiteren Skript-Neustart. Vector wird vorher nicht wiederhergestellt.
8. Zuvor aktives Vector aus dem festgelegten ZIP neu installieren, die Preinit-Regeln `xposed_file` und `xposed_data` prüfen, neu starten. Zuvor aktive microG-Promotion erst nach Google-Verifier-Prüfung aktivieren, neu starten und erneut prüfen. Diese Prüf-Neustarts sind beabsichtigt.
9. Wiederhergestellte Modulzustände, Preinit und Verifier prüfen. Eigene temporäre Firmware-/Magisk-/Post-OTA-Dateien und das zur Vector-Wiederherstellung verwendete ZIP entfernen. PC-Backups behalten. Weitere ausgewählte Phasen verwenden die neue Firmwareidentität.

Die Preinit-Prüfung gilt auch für normale Phasen 2 und 3. Vor Neustarts aus vollständig gestartetem Android wird bei vorhandenem Play Store der Verifier geprüft. In TWRP steht der Paketmanager nicht zur Verfügung; dort sichern vorherige Prüfung und deaktivierte Promotion den Übergang ab.

## Fortsetzen und Bootprobleme

Dasselbe Hauptmenü im selben Ordner starten. Ablaufplan und gerätegebundene Checkpoints wählen die restlichen Schritte. Ein bestätigter erfolgreicher Firmware-Flash wird bei späterem Fehler nicht wiederholt. Die Quellfirmware des alten Backups bleibt getrennt von der laufenden Firmware dokumentiert.

Bei gestartetem Flash ohne bestätigten Erfolg bleibt automatisches Wiederholen gesperrt. Runtime, PC-Backups und Recovery-Log behalten. Keine Checkpoints löschen oder Schreibvorgänge von Hand als abgeschlossen markieren. Ein außerhalb dieses Ablaufs manuell erfolgter Firmwarewechsel wird bewusst nicht durch Umschreiben alter Checkpoints übernommen.

Ein Boot-Timeout zeigt Diagnosehinweise. `There must be exactly one verifier` spricht für die Reparatur in `MANUAL-REPAIR.md`. Ungültige `xposed_file`-Labels oder verweigerte `dex2oat`-Ausführung erfordern die Prüfung von Magisk-Preinit und Vector-Regeln. Eine Verifier-Reparatur allein behebt fehlende SELinux-Regeln nicht. Vector bis zur erfolgreichen Prüfung deaktiviert lassen.

## Firmware und Vorschau

Vorhandene `.bin` in `FireOS-8.1.8.2.zip` umbenennen und unter `packages/root/` ablegen; nicht entpacken.

- Original: `update-kindle-karat-RS8182_user_3811_0032548774788.bin`
- Größe: **748897613 Bytes**
- SHA-256: `559cddbc9e57fa786b396aa4939b54fcb8ff85c789f0ef55df9b0ed4138c7578`
- Veröffentlichter MD5: `fcaf730cf8bfee8bc50788e24ed65d2d`
- Amazon-HTTPS-Link in `config/sources.local.json`; Firmware nicht im Paket enthalten.

```bash
bash 00_setup.sh --lang de --preview-only --steps "ALL U"
```

`--dry-run` lädt/prüft Dateien wirklich, simuliert aber Geräteaktionen. Windows akzeptiert dieselben Optionen über `00_setup.bat`.

## Prüfgrenzen

Der Firmwaredownload wurde anhand veröffentlichtem MD5, ZIP-CRC und exakten OTA-Metadaten geprüft; der SHA-256 ist festgelegt. Offline-Tests prüfen Reihenfolge, Fehlerblockaden, Wiederaufnahme, Identitätswechsel, Modulzustände sowie Preinit-/Verifier-Prüfungen. Englische/deutsche Vorschau und Bash-Syntax werden auch aus dem entpackten Release geprüft. Die zugrunde liegende manuelle Reihenfolge funktionierte auf einem 4K Plus. Die neue Automatisierung wurde nicht auf jedem Modell oder einem Windows-Gerät ausgeführt. Sämtliche Bootfehler, Stromausfälle und Hardwarefehler können Tests nicht ausschließen.
