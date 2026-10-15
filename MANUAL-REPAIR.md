# Fix a boot-logo / verifier conflict

First ensure that no flash operation is running. Interrupt only a boot-wait phase.
`adb devices -l` must list the correct Stick as `device`; otherwise resolve the USB connection first.
Replace `SERIAL_NUMBER` in every command. Enter commands individually; they work in Bash, fish and PowerShell.

Read the crash log:

```text
adb -s SERIAL_NUMBER logcat -b crash -d -t 120
```

`There must be exactly one verifier` referring to both Amazon and Google confirms the known conflict.

1. Temporarily disable the entire promotion module:

```text
adb -s SERIAL_NUMBER shell "touch /data/adb/modules/microg_installer_revived_again/disable && ls -l /data/adb/modules/microg_installer_revived_again/disable"
```

Reboot only if the file is listed:

```text
adb -s SERIAL_NUMBER reboot
```

2. Once the home screen appears, disable Google's receiver:

```text
adb -s SERIAL_NUMBER shell pm disable --user 0 com.android.vending/com.google.android.finsky.verifier.impl.PackageVerificationReceiver
adb -s SERIAL_NUMBER shell cmd package query-receivers --brief --user 0 -a android.intent.action.PACKAGE_NEEDS_VERIFICATION -t application/vnd.android.package-archive
```

Expected: `new state: disabled`, with exactly one receiver, from Amazon:
`com.amazon.adep/.nimh.receiver.PackageVerificationReceiver`.

3. Re-enable the module only if that result is confirmed:

```text
adb -s SERIAL_NUMBER shell "rm /data/adb/modules/microg_installer_revived_again/disable && echo ENABLED"
```

Reboot only after `ENABLED`:

```text
adb -s SERIAL_NUMBER reboot
```

4. After two minutes:

```text
adb -s SERIAL_NUMBER shell getprop sys.boot_completed
adb -s SERIAL_NUMBER shell cmd package query-receivers --brief --user 0 -a android.intent.action.PACKAGE_NEEDS_VERIFICATION -t application/vnd.android.package-archive
```

Expected: `1` and only Amazon. Then resume with 03_google_play_and_microg using the same checkpoint.
Zygisk Next/Vector may have been disabled after crashes: check them in Magisk, enable them and reboot if necessary.
Keep Magisk built-in Zygisk disabled.

Alternatively, explicitly run the same repair through the script (requires root ADB and an existing checkpoint).
Linux:

```text
bash 03_google_play_and_microg.sh --serial SERIAL_NUMBER --repair-verifier
```

Windows:

```text
03_google_play_and_microg.bat --serial SERIAL_NUMBER --repair-verifier
```

This does not repeat promotion/flash installation or remove the Play Store system copy.
Repair remains blocked if a `pending` write operation is uncertain. Do not delete the checkpoint.
