"""Restore Wi-Fi only after confirming Android and both OTA blocks."""
import contextlib
import io
import tempfile
import unittest
from unittest.mock import Mock,patch
import karat as k

OTA='package:com.amazon.device.software.ota\npackage:com.amazon.device.software.ota.override'
class WifiRestore(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.log=Mock();self.s.state={'done':[],'pending':None}
        self.s.prop=Mock(side_effect=lambda key:'1' if key=='sys.boot_completed' else '')
        self.s.shell=Mock(side_effect=[OTA,'','1'])
    def test_check_ota_before_enabling_and_verify_wifi(self):
        self.assertTrue(self.s.restore_wifi())
        self.assertEqual([c.args[0] for c in self.s.shell.call_args_list],['pm list packages -d --user 0','svc wifi enable','settings get global wifi_on'])
    def test_missing_ota_block_keeps_wifi_off(self):
        self.s.shell=Mock(return_value='package:com.amazon.device.software.ota')
        self.assertFalse(self.s.restore_wifi());self.s.shell.assert_called_once_with('pm list packages -d --user 0')
    def test_no_wifi_command_in_recovery(self):
        self.s.prop=Mock(return_value='3.7.1_12-0');self.assertFalse(self.s.restore_wifi());self.s.shell.assert_not_called()
    def test_no_wifi_command_before_android_boot(self):
        self.s.prop=Mock(return_value='');self.assertFalse(self.s.restore_wifi());self.s.shell.assert_not_called()
    def test_failure_warns_and_allows_setup_to_continue(self):
        self.s.shell=Mock(side_effect=k.Stop('service unavailable'))
        self.assertFalse(self.s.restore_wifi());self.assertIn('Setup will continue',self.s.log.call_args.args[0])
    def test_enable_confirmation_can_be_delayed(self):
        self.s.shell=Mock(side_effect=[OTA,'','0','1'])
        with patch.object(k.time,'sleep') as sleep:self.assertTrue(self.s.restore_wifi())
        sleep.assert_called_once_with(1)
    def test_timeout_warns_without_aborting(self):
        self.s.shell=Mock(side_effect=[OTA,''])
        with patch.object(k.time,'monotonic',side_effect=[0,16]):self.assertFalse(self.s.restore_wifi())
        self.assertIn('Setup will continue',self.s.log.call_args.args[0])
    def test_temporary_phase_restores_wifi_after_ota_verification(self):
        self.s.probe_temporary_root=Mock(return_value=True)
        self.s.temporary_su=Mock(side_effect=['uid=0(root)','new state: disabled','new state: disabled'])
        self.s.shell=Mock(return_value=OTA);self.s.restore_wifi=Mock()
        self.s.temporary_root();self.s.restore_wifi.assert_called_once()
    def test_failed_ota_block_does_not_restore_wifi(self):
        self.s.probe_temporary_root=Mock(return_value=True)
        self.s.temporary_su=Mock(side_effect=['uid=0(root)','new state: disabled','new state: disabled'])
        self.s.shell=Mock(return_value='');self.s.restore_wifi=Mock()
        with self.assertRaises(k.Stop):self.s.temporary_root()
        self.s.restore_wifi.assert_not_called()
    def test_permanent_resume_restores_after_postota_boot(self):
        self.s.state['done']=['unlock','backup','postota','postota-boot','magisk','magisk-boot','magisk-ui','magisk-setup-boot','permanent-cleanup']
        self.s.resume_postota_preflight=Mock();self.s.ensure_preinit=Mock();events=[]
        self.s.stage=Mock(side_effect=lambda name,*args,**kw:events.append(name))
        self.s.restore_wifi=Mock(side_effect=lambda:events.append('wifi'))
        self.s.shell=Mock(return_value='30.7:MAGISK:R')
        self.s.permanent_root()
        self.assertEqual(events[events.index('postota-boot')+1],'wifi')
        self.assertLess(events.index('wifi'),events.index('magisk'))
