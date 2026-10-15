"""Regression for ROOTED being emitted before the embedded su daemon is ready."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import zipfile
import karat as k
import setup_menu

class GhostReady(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.statefile=self.s.work/'TEST.json';self.s.state={'serial':'TEST','done':[],'pending':None};self.s.log=Mock();self.s.save()
        self.s.reboot=Mock();self.s.push=Mock()
        payload=Path(self.tmp.name)/'ghost.zip'
        with zipfile.ZipFile(payload,'w') as z:z.writestr('ghostlock-karat-v1.0.4/bin/preload',b'placeholder')
        self.s.file=Mock(return_value=payload)
    def android(self,key):return '1' if key=='sys.boot_completed' else ''
    def test_missing_standard_su_falls_back_to_local_client(self):
        self.s.shell=Mock(side_effect=['su: inaccessible or not found','uid=0(root) gid=0(root)'])
        self.assertTrue(self.s.probe_temporary_root());self.assertEqual(self.s.temporary_su_client,'/data/local/tmp/su')
        self.assertTrue(all(c.kwargs['check'] is False for c in self.s.shell.call_args_list))
    def test_nonroot_client_is_not_accepted(self):
        self.s.shell=Mock(return_value='uid=2000(shell)');self.assertFalse(self.s.probe_temporary_root())
    def test_selected_client_is_used_for_ota_and_unlock_commands(self):
        self.s.temporary_su_client='/data/local/tmp/su';self.s.shell=Mock(return_value='OK')
        self.s.temporary_su('pm disable --user 0 package.example')
        self.assertEqual(self.s.shell.call_args.args[0],"/data/local/tmp/su -c 'pm disable --user 0 package.example'")
    def test_early_rooted_marker_waits_for_daemon(self):
        self.s.shell=Mock(side_effect=lambda command,**kw:'ROOTED uid=0 euid=0' if command.startswith('cat /data/local/tmp/ghostlock.proof') else '')
        self.s.probe_temporary_root=Mock(side_effect=[False,False,True])
        with patch.object(k.time,'sleep'):self.assertTrue(self.s.ghost_attempt())
        self.assertEqual(self.s.probe_temporary_root.call_count,3)
        self.assertIsNone(self.s.state['pending']);self.assertNotIn('ghostlock_attempts',self.s.state)
        self.s.reboot.assert_called_once()
    def test_pending_ghostlock_reuses_actual_root_without_exploit(self):
        self.s.state['pending']='ghostlock';self.s.state['ghostlock_attempts']=1
        self.s.prop=Mock(side_effect=self.android);self.s.probe_temporary_root=Mock(return_value=True)
        self.s.resume_ghostlock();self.s.reboot.assert_not_called()
        self.assertIsNone(self.s.state['pending']);self.assertTrue(self.s.ghost_resume_authorized)
    def test_pending_ghostlock_reboot_precedes_clearing_state(self):
        self.s.state['pending']='ghostlock';self.s.prop=Mock(side_effect=self.android);self.s.probe_temporary_root=Mock(return_value=False)
        def reboot():self.assertEqual(self.s.state['pending'],'ghostlock')
        self.s.reboot=Mock(side_effect=reboot)
        with patch.object(k.time,'monotonic',side_effect=[0,31]):self.s.resume_ghostlock()
        self.assertIsNone(self.s.state['pending']);self.assertEqual(self.s.state['ghostlock_attempts'],1)
        self.assertTrue(self.s.ghost_reboot_ready)
    def test_failed_resume_reboot_keeps_pending(self):
        self.s.state['pending']='ghostlock';self.s.prop=Mock(side_effect=self.android);self.s.probe_temporary_root=Mock(return_value=False)
        self.s.reboot=Mock(side_effect=k.Stop('boot timeout'))
        with patch.object(k.time,'monotonic',side_effect=[0,31]),self.assertRaises(k.Stop):self.s.resume_ghostlock()
        self.assertEqual(self.s.state['pending'],'ghostlock')
    def test_other_pending_writes_are_not_cleared(self):
        self.s.state['pending']='postota';self.s.resume_ghostlock();self.assertEqual(self.s.state['pending'],'postota')
        self.s.reboot.assert_not_called()
    def test_two_attempt_limit_survives_restart(self):
        self.s.state['pending']='ghostlock';self.s.state['ghostlock_attempts']=2
        self.s.prop=Mock(side_effect=self.android);self.s.probe_temporary_root=Mock(return_value=False)
        with patch.object(k.time,'monotonic',side_effect=[0,31]),self.assertRaises(k.Stop):self.s.resume_ghostlock()
        self.s.reboot.assert_not_called();self.assertEqual(self.s.state['pending'],'ghostlock')
    def test_legacy_ghostlock_checkpoint_is_found_by_main_menu(self):
        self.s.state['pending']='ghostlock';self.s.save()
        self.assertEqual(setup_menu.resume_choice(self.s.base,'TEST')[0],['1'])
if __name__=='__main__':unittest.main()
