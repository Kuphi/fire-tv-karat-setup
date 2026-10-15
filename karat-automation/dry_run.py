#!/usr/bin/env python3
"""Presentation-only simulation: no ADB, network, checkpoints or filesystem writes."""
import terminal_ui as ui

def preview(flow, scenario='success', downloads=False, phase='all', selected_apps=None):
    def log(text):
        ui.event(text)
    ui.title('PREVIEW · '+flow.upper(), 'Simulated data · no real device step will run')
    log('DOWNLOAD TEST: Files were really downloaded/checked; the following device output is simulated.' if downloads else 'PREVIEW: No commands, downloads or writes.')
    log('Device: Example Stick · Serial number: DEMO · Firmware: example profile')
    if flow == 'root' and phase == 'update':
        for text in (
            'Verify the pinned firmware file and karat identity.',
            'Reuse verified unlock and PC backup, or unlock and create the backup once.',
            'Disable Google verifier if installed; preserve and disable Vector/microG module states.',
            'One TWRP session: firmware → Post-OTA → Magisk; no intermediate Android boot.',
            'Boot Android, restore Wi-Fi after OTA checks; install the full local Magisk app.',
            'Magisk Direct Install → scripted reboot → verify writable preinit storage.',
            'Restore previously enabled Vector; verify SELinux rules before reboot.',
            'Disable/check Google verifier → restore previously enabled microG → reboot → check.',
            'Verify target firmware and clean only setup-owned temporary device files.'):
            log(text+' [simulated]')
        log('Uncertain flashes remain blocked; restarting the main menu resumes verified checkpoints.')
        return 0
    if flow == 'root':
        log('Root phase: '+phase+' [simulated]')
        for name, detail in [
            ('Check files','Local APKs and ZIPs checked (simulated).'),
            ('temporary-root','GhostLock attempt 1/2 → temporary root and OTA blocking (simulated).'),
            ('unlock','Unlock the bootloader → Unlock OK (simulated).'),
            ('backup','Back up Boot/Data/System and Vendor to the PC; check SHA256 (simulated).'),
            ('postota','Install Post-OTA and confirm Android boot (simulated).'),
            ('magisk-ui','Install the full local Magisk app; APK hash confirmed (simulated).'),
            ('magisk-setup-boot','After RESUME: reboot automatically, wait for Android and verify Magisk (simulated).'),
            ('framework','Install Zygisk Next and Vector; FakeGApps → System Framework.'),
            ('google-apks','Install microG and Play Store; disable the Google verifier.'),
            ('microg-promotion','Before promotion: exactly one receiver – Amazon (simulated).'),
        ]:
            temporary={'Check files','temporary-root'}
            permanent={'Check files','temporary-root','unlock','backup','postota','magisk-ui','magisk-setup-boot'}
            google={'Check files','framework','google-apks','microg-promotion'}
            allowed=temporary if phase=='temporary' else permanent if phase=='permanent' else google if phase=='google' else None
            if allowed is None or name in allowed:
                log('START: '+name);log(detail);log('OK: '+name)
        if phase in ('temporary','permanent'):
            log('START: Phase cleanup')
            log('No sdcard files created.' if phase=='temporary' else 'Remove setup-owned device backups after verifying PC copies with SHA256, and Magisk/Post-OTA ZIPs (simulated).')
            log('OK: Root subphase completed.')
            print('\n  END OF PREVIEW · no real setup step performed\n')
            return 0
        print('\n┌─ IMMEDIATELY BEFORE THE MICROG REBOOT ───────────────────────────')
        log('Google verifier: new state: disabled (simulated)')
        log('1 receivers found: com.amazon.adep/.nimh.receiver.PackageVerificationReceiver (simulated)')
        print('└──────────────────────────────────────────────────────────\n')
        log('START: microg-boot')
        if scenario == 'boot-timeout':
            log('Waiting for Android boot_completed=1 … [6 minutes in a real run]')
            log('STOP: Boot timeout (simulated). No further flash.')
            log('BOOT HELP: Possible verifier conflict; check the crash log and USB connection first.')
            log('Explicitly requested repair: 03_google_play_and_microg --serial SERIAL_NUMBER --repair-verifier')
            log('Disable module → reboot → disable/check Google verifier → enable module → reboot → check.')
            log('See MANUAL-REPAIR.md; preserve checkpoints.')
        else:
            log('Android: boot_completed=1; only Amazon verifier after boot (simulated).')
            log('OK: microg-boot')
            log('START: root-cleanup')
            log('Delete temporary Google module files; the one-time backup was already saved in phase 2 (simulated).')
            log('OK: root-cleanup')
            log('OK: ROOT/FRAMEWORK COMPLETE. Enable microG registration and Cloud Messaging yourself.')
    elif flow == 'emotn':
        for name, detail in [
            ('Install Emotn','Install APK and helpers (simulated).'),
            ('Set up the launcher','Set Emotn as Home; open Settings Bridge (simulated).'),
            ('Vector scope','Scope System Clock/Idle Timer/App Categories ONLY to Emotn UI; clock follows the device timezone, including changes; weather town: your own town.'),
        ]:
            log('START: '+name);log(detail);log('OK: '+name)
        log('Prompt in a real run: RESUME = continue · EXIT = exit')
        log('OK: EMOTN COMPLETE.')
    else:
        chosen=selected_apps if selected_apps is not None else ['Netflix','YouTube','Prime Video','Disney+','Wholphin','CX File Explorer','Emotn App Categories']
        log('Selected apps: '+(', '.join(chosen) or 'none'))
        log('START: Set animation scales to 0.5')
        log('OK: Animations')
        for name in chosen:
            source='Amazon Appstore' if name in ('Netflix','YouTube','Prime Video','Disney+') else 'official GitHub download' if name=='Wholphin' else 'Helper / Vector' if name=='Emotn App Categories' else 'Play Store / local APK'
            log('START: '+name+' → '+source+' [simulated]')
            log('In a real run: confirm the store/Vector action, then RESUME or EXIT.')
        log('START: Optimize Emotn and selected installed apps')
        log('OK: compile -m speed -f [simulated]')
        log('Store installations and optimizations were not actually performed here.')
        log('OK: App setup preview completed.')
    print('\n════════════════════════════════════════════════════════════')
    print('  END OF PREVIEW · no real setup step performed')
    print('════════════════════════════════════════════════════════════\n')
    return 0
