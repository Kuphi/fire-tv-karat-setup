"""Post-OTA resume safety: no automatic repetition of an uncertain write."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import karat as k

class PostotaResume(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):
            self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.statefile=self.s.work/'TEST.json'
        self.s.state={'serial':'TEST','done':['unlock','backup'],'pending':'postota'}
        self.s.save();self.s.log=Mock();self.s.verify_backups=Mock()
        self.s.prop=Mock(return_value='3.7.1_12-0')
    def old_log(self,serial='TEST',error='adbd-Bytecheck 610743 falsch. Kein Post-OTA-Flash.',extra='',known=True):
        digest='d30fef3c2ee17dc4c2a57865fd984664775a156f2c918af8511bebde153abc87' if known else 'unknown'
        p=self.s.work/'20200101-010000-root.log'
        p.write_text(f'[2020-01-01T01:00:00+01:00] HOST: Python=3.14.7; Skript-SHA256={digest}\n'
                     '[2020-01-01T01:00:01+01:00] START: postota\n'
                     f"[2020-01-01T01:00:02+01:00] $ adb -s {serial} shell 'dd if=/mnt/postota-check/system/apex/com.android.adbd/bin/adbd'\n"
                     +extra+f'[2020-01-01T01:00:03+01:00] STOP: Stufe=postota; Pending=postota; {error}\n')
        return p
    def test_proven_old_preflight_rejection_is_rechecked_not_completed(self):
        self.old_log();self.s.resume_postota_preflight()
        self.assertIsNone(self.s.state['pending']);self.assertNotIn('postota',self.s.state['done'])
        self.assertEqual(json.loads(self.s.statefile.with_suffix('.json.before-postota-resume').read_text())['pending'],'postota')
        self.s.verify_backups.assert_called_once()
    def test_backup_diagnostics_alone_cannot_clear_pending(self):
        p=self.s.work/'20200101-010000-root.log'
        p.write_text('[2020-01-01T01:00:00+01:00] STOP: Stufe=None; Pending=postota; Unklarer Schreibvorgang.\nBackup Complete\nDone processing script file\n')
        self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
    def test_old_install_command_keeps_pending(self):
        self.old_log(extra="[2020-01-01T01:00:02+01:00] $ adb -s TEST shell 'twrp install /sdcard/post-ota-karat-v1.0.0.zip'\n")
        self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
        self.s.verify_backups.assert_not_called()
    def test_unknown_source_is_not_adopted(self):
        self.old_log(known=False);self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
    def test_missing_or_truncated_log_is_not_adopted(self):
        p=self.old_log();p.write_text(p.read_text().split('STOP:')[0])
        self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
    def test_different_device_log_cannot_clear_pending(self):
        self.old_log(serial='OTHER');self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
    def test_prewrite_command_failure_is_rechecked(self):
        self.old_log(error='Befehl fehlgeschlagen (Exit 1).')
        self.s.resume_postota_preflight();self.assertIsNone(self.s.state['pending'])
        self.assertNotIn('postota',self.s.state['done'])
    def test_different_error_cannot_clear_pending(self):
        self.old_log(error='Installer meldet keinen eindeutigen Erfolg. In TWRP bleiben!')
        self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
    def test_newer_ambiguous_attempt_blocks_old_evidence(self):
        p=self.old_log();text=p.read_text().split('STOP:')[0]
        (self.s.work/'20200102-010000-root.log').write_text(text)
        self.s.resume_postota_preflight();self.assertEqual(self.s.state['pending'],'postota')
    def test_backup_failure_does_not_clear_pending(self):
        self.old_log();self.s.verify_backups.side_effect=k.Stop('backup invalid')
        with self.assertRaises(k.Stop):self.s.resume_postota_preflight()
        self.assertEqual(self.s.state['pending'],'postota')
    def test_new_preflight_failure_does_not_mark_a_write(self):
        self.s.state['pending']=None;self.s.verify_backups.side_effect=k.Stop('backup invalid')
        with self.assertRaises(k.Stop):self.s.stage('postota',self.s.postota)
        self.assertIsNone(self.s.state['pending']);self.assertNotIn('postota',self.s.state['done'])
    def test_transfer_failure_does_not_mark_a_write(self):
        self.s.state['pending']=None;self.s.active_stage='postota'
        self.s.recovery_ready=Mock();self.s.file=Mock(return_value=Path('payload.zip'))
        self.s.push=Mock(side_effect=k.Stop('transfer invalid'));self.s.shell=Mock()
        with self.assertRaises(k.Stop):self.s.flash('post-ota-karat-v1.0.0.zip','- info done')
        self.assertIsNone(self.s.state['pending']);self.s.shell.assert_not_called()
    def test_installer_failure_retains_pending(self):
        self.s.state['pending']=None;self.s.active_stage='postota'
        self.s.recovery_ready=Mock();self.s.file=Mock(return_value=Path('payload.zip'));self.s.push=Mock()
        def install(*args,**kwargs):
            self.assertEqual(json.loads(self.s.statefile.read_text())['pending'],'postota')
            raise k.Stop('installer failed')
        self.s.shell=Mock(side_effect=install)
        with self.assertRaises(k.Stop):self.s.flash('post-ota-karat-v1.0.0.zip','- info done')
        self.assertEqual(self.s.state['pending'],'postota')
    def test_successful_stage_completes_once(self):
        self.s.state['pending']=None;self.s.recovery_ready=Mock()
        self.s.file=Mock(return_value=Path('payload.zip'));self.s.push=Mock();self.s.shell=Mock(return_value='- info done')
        fn=lambda:self.s.flash('post-ota-karat-v1.0.0.zip','- info done')
        self.s.stage('postota',fn);self.s.stage('postota',fn)
        self.s.shell.assert_called_once();self.assertIsNone(self.s.state['pending'])
        self.assertIn('postota',self.s.state['done'])
if __name__=='__main__':unittest.main()
