"""Skip manual confirmation for the default; detect actual incompatible settings."""
import contextlib
import io
import tempfile
import unittest
from unittest.mock import Mock
import karat as k

class ZygiskSetting(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.log=Mock();self.s.shell=Mock(return_value='enabled=0');self.s.pause=Mock();self.s.reboot=Mock();self.s.root_ok=Mock()
    def test_default_off_has_no_prompt_app_or_reboot(self):
        self.s.ensure_builtin_zygisk_off();self.s.shell.assert_called_once();self.s.pause.assert_not_called();self.s.reboot.assert_not_called()
        self.assertIn('COALESCE',self.s.shell.call_args.args[0])
    def test_enabled_opens_resolved_magisk_then_checks_and_reboots(self):
        self.s.shell.side_effect=['enabled=1','com.topjohnwu.magisk/.MainActivity','enabled=0']
        self.s.ensure_builtin_zygisk_off();self.assertIn('am start -W -n com.topjohnwu.magisk/.MainActivity',self.s.pause.call_args.args[2]);self.s.reboot.assert_called_once();self.s.root_ok.assert_called_once()
    def test_still_enabled_prompts_again_before_reboot(self):
        self.s.shell.side_effect=['enabled=1','com.topjohnwu.magisk/.MainActivity','enabled=1','com.topjohnwu.magisk/.MainActivity','enabled=0']
        self.s.ensure_builtin_zygisk_off();self.assertEqual(self.s.pause.call_count,2);self.s.reboot.assert_called_once()
    def test_invalid_query_output_never_installs_or_confirms(self):
        for value in ('','error','enabled=2','enabled=0\nenabled=1'):
            self.s.shell=Mock(return_value=value)
            with self.assertRaises(k.Stop):self.s.ensure_builtin_zygisk_off()
        self.s.pause.assert_not_called();self.s.reboot.assert_not_called()
    def test_sql_failure_is_not_assumed_disabled(self):
        self.s.shell.side_effect=k.Stop('query failed')
        with self.assertRaises(k.Stop):self.s.ensure_builtin_zygisk_off()
        self.s.pause.assert_not_called()
    def test_legacy_flag_does_not_bypass_enabled_setting(self):
        self.s.a.zygisk_off=True
        self.s.shell.side_effect=['enabled=1','com.topjohnwu.magisk/.MainActivity','enabled=0']
        self.s.pause.side_effect=lambda *a:self.assertFalse(self.s.a.zygisk_off)
        self.s.ensure_builtin_zygisk_off();self.assertTrue(self.s.a.zygisk_off);self.s.pause.assert_called_once()
    def test_missing_app_does_not_attempt_wrong_activity(self):
        self.s.shell.side_effect=['enabled=1','No activity found']
        with self.assertRaises(k.Stop):self.s.ensure_builtin_zygisk_off()
        self.s.pause.assert_not_called();self.s.reboot.assert_not_called()
    def test_exit_does_not_reboot_and_restores_flag(self):
        self.s.a.zygisk_off=True;self.s.shell.side_effect=['enabled=1','com.topjohnwu.magisk/.MainActivity'];self.s.pause.side_effect=k.Stop('exit')
        with self.assertRaises(k.Stop):self.s.ensure_builtin_zygisk_off()
        self.assertTrue(self.s.a.zygisk_off);self.s.reboot.assert_not_called()
