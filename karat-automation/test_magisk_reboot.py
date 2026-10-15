"""Magisk setup reboots from the terminal and resumes without re-flashing."""
import contextlib
import io
import tempfile
import unittest
from unittest.mock import Mock
import karat as k

class MagiskReboot(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):
            self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close); self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST'; self.s.state={'serial':'TEST','done':[], 'pending':None}
        self.s.statefile=self.s.work/'TEST.json'; self.s.log=Mock()
        self.s.ensure_preinit=Mock()
        self.events=[]
        self.s.reboot=Mock(side_effect=lambda:self.events.append('reboot'))
        self.s.root_ok=Mock(side_effect=lambda:self.events.append('root'))
        self.s.shell=Mock(side_effect=lambda cmd:self.events.append(cmd) or '30.7:MAGISK:R')
        self.s.file=Mock(return_value='local-apk')
        self.s.verify_magisk_app=Mock(side_effect=lambda apk:self.events.append(apk))
    def test_reboot_then_verify_root_version_and_full_app(self):
        self.s.stage('magisk-setup-boot',self.s.magisk_setup_reboot)
        self.assertEqual(self.events,['reboot','root','magisk -v','local-apk'])
        self.assertIn('magisk-setup-boot',self.s.state['done'])
    def test_completed_reboot_not_repeated(self):
        self.s.state['done']=['magisk-setup-boot']
        self.s.stage('magisk-setup-boot',self.s.magisk_setup_reboot)
        self.s.reboot.assert_not_called()
    def test_boot_failure_not_marked_complete(self):
        self.s.reboot.side_effect=k.Stop('boot timeout')
        with self.assertRaises(k.Stop):self.s.stage('magisk-setup-boot',self.s.magisk_setup_reboot)
        self.assertNotIn('magisk-setup-boot',self.s.state['done']);self.s.root_ok.assert_not_called()
    def test_wrong_magisk_version_not_marked_complete(self):
        self.s.shell=Mock(return_value='wrong version')
        with self.assertRaises(k.Stop):self.s.stage('magisk-setup-boot',self.s.magisk_setup_reboot)
        self.assertNotIn('magisk-setup-boot',self.s.state['done']);self.s.verify_magisk_app.assert_not_called()
    def test_older_phase_two_runs_only_new_reboot(self):
        self.s.state['done']=['unlock','backup','postota','postota-boot','magisk','magisk-boot','magisk-ui','permanent-cleanup']
        self.s.resume_postota_preflight=Mock()
        self.s.permanent_root()
        self.s.reboot.assert_called_once_with()
        self.assertIn('magisk-setup-boot',self.s.state['done'])
