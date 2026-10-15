"""Explicit, resumable Fire OS update; uncertain flash writes are never replayed."""
import re
import zipfile

FIRMWARE = 'FireOS-8.1.8.2.zip'
URL = 'https://d1s31zyz7dcc2d.cloudfront.prod.ota-cloudfront.net/2026/8/17/6b5b010d-ab55-4b17-8247-6870c688776e/update-kindle-karat-RS8182_user_3811_0032548774788.bin'
SHA256 = '559cddbc9e57fa786b396aa4939b54fcb8ff85c789f0ef55df9b0ed4138c7578'
FINGERPRINT = 'Amazon/karat/karat:11/RS8182.3811N/0032548774788:user/amz-p,release-keys'
MODULES = ('zygisk_vector', 'microg_installer_revived_again')
PREFIX = 'update-8182-'

class FirmwareUpdate:
    def require_preinit(self):
        from karat import require
        require(self.shell('p=$(magisk --path); test -n "$p" && test -d "$p/.magisk/preinit" && test -w "$p/.magisk/preinit" && echo PREINIT_READY', check=False) == 'PREINIT_READY',
                'Magisk preinit is missing. Vector must remain disabled; complete Magisk Direct Install and reboot first.')

    def ensure_preinit(self):
        from karat import Stop
        while True:
            try:
                self.require_preinit()
                return
            except Stop:
                self.log('Magisk needs Direct Install to create preinit storage. Keep Vector and microG promotion disabled until verification succeeds.')
                old = self.a.magisk_ready
                self.a.magisk_ready = False
                try:
                    self.magisk_app()
                finally:
                    self.a.magisk_ready = old
                self.magisk_setup_reboot()

    def verify_vector_policy(self):
        from karat import require
        self.require_preinit()
        out = self.shell('p=$(magisk --path); cat "$p/.magisk/preinit/sepolicy.rule"', check=False)
        require(all(re.search(r'^type '+name+r' file_type\s*$', out, re.M) for name in ('xposed_file', 'xposed_data')),
                'Vector SELinux rules are missing from Magisk preinit. Reboot is blocked.')

    def update_identity_transition(self, profile):
        tx = self.state.get('firmware_update', {})
        return (isinstance(tx, dict) and tx.get('target') == FINGERPRINT
                and profile.get('fingerprint') == FINGERPRINT
                and PREFIX+'firmware' in self.state['done']
                and self.state.get('profile') == tx.get('source_profile'))

    def update_backup_fingerprint(self):
        tx = self.state.get('firmware_update', {})
        if isinstance(tx, dict) and tx.get('target') == FINGERPRINT:
            return tx.get('source_profile', {}).get('fingerprint')
        return None

    def update_modules_off(self):
        from karat import require
        # Do not interrupt a pending module installation with a firmware update.
        require(not self.shell('find /data/adb/modules_update -name module.prop 2>/dev/null', check=False).strip(),
                'Pending Magisk module updates exist. Finish their normal reboot before starting the firmware update.')
        tx = self.state['firmware_update']
        if 'restore_modules' not in tx:
            restore = []
            for module in MODULES:
                path = '/data/adb/modules/'+module
                out = self.shell('if [ -f '+path+'/module.prop ] && [ ! -f '+path+'/disable ] && [ ! -f '+path+'/remove ]; then echo ENABLED; fi')
                if out == 'ENABLED': restore.append(module)
            # Save intent before changing flags so an interruption cannot lose it.
            tx['restore_modules'] = restore
            self.save()
        for module in MODULES:
            path = '/data/adb/modules/'+module
            self.shell('if [ -f '+path+'/module.prop ]; then touch '+path+'/disable && test -f '+path+'/disable; fi')
        self.shell('sync')

    def update_firmware_flash(self):
        from karat import require
        self.verify_backups()
        path = self.file(FIRMWARE)
        with zipfile.ZipFile(path) as z:
            metadata = dict(line.split('=', 1) for line in z.read('META-INF/com/android/metadata').decode().splitlines() if '=' in line)
            require(metadata.get('post-build') == FINGERPRINT and metadata.get('pre-device') == 'karat',
                    'Wrong firmware target in OTA metadata.')
        free = self.shell("df -k /sdcard | tail -n 1 | awk '{print $4}'")
        require(free.isdigit() and int(free)*1024 >= path.stat().st_size + 64*1024**2,
                'Not enough free internal storage for the firmware ZIP; no flash started.')
        self.flash(FIRMWARE, 'script succeeded: result was [1.000000]')

    def update_restore_vector(self):
        self.ensure_preinit()
        self.module('google-play/vector.zip')
        self.verify_vector_policy()

    def update_restore_microg(self):
        self.verifier()
        self.shell('rm -f /data/adb/modules/microg_installer_revived_again/disable && sync')

    def update_cleanup(self):
        self.root_cleanup('permanent')
        self.shell('rm -f /sdcard/'+FIRMWARE)
        if 'zygisk_vector' in self.state['firmware_update'].get('restore_modules', []):
            self.shell('rm -f /sdcard/google-play/vector.zip; rmdir /sdcard/google-play 2>/dev/null || :')

    def update_flow(self):
        from karat import require
        tx = self.state.get('firmware_update')
        if tx is not None:
            require(isinstance(tx, dict) and tx.get('target') == FINGERPRINT and isinstance(tx.get('source_profile'), dict), 'Invalid firmware update checkpoint.')
            restore = tx.get('restore_modules', [])
            require(isinstance(restore, list) and all(m in MODULES for m in restore) and len(restore) == len(set(restore)), 'Invalid saved module states.')
        if tx and PREFIX+'complete' in self.state['done']:
            require(self.state['profile']['fingerprint'] == FINGERPRINT, 'Completed update does not match this firmware.')
            self.log('Fire OS 8.1.8.2 update already completed; no flash or reboot repeated.')
            return
        if self.state.get('pending') == 'unlock' and self.prop('ro.twrp.version') == '3.7.1_12-0':
            self.finish('unlock')
        require(not self.state.get('pending'), 'Uncertain flash operation: preserve checkpoints and recovery log; no automatic repeat flash.')
        if not tx:
            source = self.state['profile']
            require(int(source['incremental']) < 32548774788,
                    'U only upgrades older firmware to 8.1.8.2. Already current or newer firmware will not be flashed.')
            self.confirm('UPDATE', 'Install Fire OS 8.1.8.2 using unlocked karat TWRP. Keep USB and power connected. The verified PC backup will be preserved.')
            tx = {'target': FINGERPRINT, 'source_profile': dict(source)}
            self.state['firmware_update'] = tx
            self.save()
        if PREFIX+'firmware' not in self.state['done']:
            if not self.prop('ro.twrp.version'):
                require(self.prop('sys.boot_completed') == '1', 'Start U from fully booted Android or the verified TWRP checkpoint.')
                if self.shell('pm path com.android.vending', check=False).startswith('package:'): self.verifier()
            if 'unlock' not in self.state['done']:
                if '30.7:' in self.shell('magisk -v', check=False):
                    self.root_ok()
                    self.verifying_existing = True
                    self.reboot(True)
                    self.finish('unlock')
                    self.verifying_existing = False
                else:
                    require('uid=0(' not in self.shell('id'), 'Unknown rooted installation without Magisk 30.7; no automatic repeat unlock.')
                    self.stage('unlock', self.unlock)
            if not self.prop('ro.twrp.version'): self.reboot(True)
            self.recovery_ready()
            self.stage('backup', self.backups)
            self.verify_backups()
            self.cleanup()  # PC copies verified; only setup-owned device backups removed
            self.stage(PREFIX+'modules-off', self.update_modules_off)
            self.stage(PREFIX+'firmware', self.update_firmware_flash)
        if PREFIX+'magisk' not in self.state['done']:
            require(self.prop('ro.twrp.version') == '3.7.1_12-0', 'Remain in TWRP until Post-OTA and Magisk have both completed.')
        self.stage(PREFIX+'postota', self.postota)
        self.stage(PREFIX+'magisk', lambda: self.flash('Magisk-v30.7.apk', '- Done'))
        self.stage(PREFIX+'boot', lambda: (self.reboot(), self.root_ok()))
        require(self.state['profile']['fingerprint'] == FINGERPRINT, 'The updated firmware did not boot.')
        require('30.7:' in self.shell('magisk -v'), 'Magisk 30.7 is required after updating.')
        self.restore_wifi()
        self.stage(PREFIX+'app', self.magisk_app)
        self.stage(PREFIX+'setup-boot', self.magisk_setup_reboot)
        self.ensure_preinit()
        restore = tx.get('restore_modules', [])
        if 'zygisk_vector' in restore:
            self.stage(PREFIX+'vector', self.update_restore_vector)
            if PREFIX+'vector-boot' not in self.state['done']: self.verify_vector_policy()
            self.stage(PREFIX+'vector-boot', self.reboot)
        if 'microg_installer_revived_again' in restore:
            self.stage(PREFIX+'microg', self.update_restore_microg)
            self.stage(PREFIX+'microg-boot', self.microg_reboot)
        self.require_preinit()
        for module in restore:
            path = '/data/adb/modules/'+module
            require(self.shell('test -f '+path+'/module.prop && test ! -f '+path+'/disable && test ! -f '+path+'/remove && echo MODULE_ENABLED') == 'MODULE_ENABLED',
                    'A previously enabled module is not enabled after the update: '+module)
        if 'zygisk_vector' in restore: self.verify_vector_policy()
        if self.shell('pm path com.android.vending', check=False).startswith('package:'): self.verifier()
        self.stage(PREFIX+'cleanup', self.update_cleanup)
        for name in ('postota','postota-boot','magisk','magisk-boot','magisk-ui','magisk-setup-boot','permanent-cleanup'):
            self.finish(name)
        self.finish(PREFIX+'complete')
        self.log('Fire OS 8.1.8.2, Magisk preinit and previously enabled modules verified. Update completed.')
