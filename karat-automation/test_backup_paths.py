"""Legacy Windows backup manifests must validate without a second backup."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import karat as k

class BackupPaths(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):
            self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.state={'profile':{'fingerprint':'test-profile'}}
        self.s.backup=Path(self.tmp.name)/'backups/TEST/automation-before-root'
        self.s.backup.mkdir(parents=True);self.s.log=Mock()
        self.files={}
        for name in ('twrp/auto-before-persistent-root/boot.emmc.win','twrp/auto-before-persistent-root/data.ext4.win000','twrp/auto-before-post-ota/system.ext4.win','vendor-before-post-ota.img'):
            p=self.s.backup/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
            self.files[name]=k.sha(p)
    def manifest(self,files):
        p=self.s.backup/'verified.json'
        p.write_text(json.dumps({'serial':'TEST','fingerprint':'test-profile','files':files}))
        return p
    def test_old_windows_manifest_validates_without_rewriting(self):
        files={name.replace('/','\\'):digest for name,digest in self.files.items()}
        p=self.manifest(files);before=p.read_bytes();self.s.verify_backups()
        self.assertEqual(p.read_bytes(),before)
    def test_portable_manifest_validates(self):
        self.manifest(self.files);self.s.verify_backups()
    def test_missing_backup_is_still_rejected(self):
        self.manifest({name.replace('/','\\'):digest for name,digest in self.files.items()})
        (self.s.backup/'twrp/auto-before-persistent-root/boot.emmc.win').unlink()
        with self.assertRaises(k.Stop):self.s.verify_backups()
    def test_changed_backup_is_still_rejected(self):
        self.manifest({name.replace('/','\\'):digest for name,digest in self.files.items()})
        (self.s.backup/'twrp/auto-before-post-ota/system.ext4.win').write_bytes(b'changed')
        with self.assertRaises(k.Stop):self.s.verify_backups()
    def test_windows_traversal_is_rejected(self):
        self.manifest({**self.files,'twrp\\..\\..\\private': 'unknown'})
        with self.assertRaises(k.Stop):self.s.verify_backups()
if __name__=='__main__':unittest.main()
