import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
import karat as k
import setup_menu as menu

class Phases(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.state={'serial':'TEST','done':[],'pending':None};self.s.statefile=self.s.work/'TEST.json'
        self.s.log=Mock();self.s.prepare=Mock();self.s.connect=Mock();self.s.root_ok=Mock()
        self.s.prop=Mock(side_effect=lambda key:'1' if key=='sys.boot_completed' else '')
        self.s.shell=Mock(return_value='30.7:MAGISK:R')
    def test_temporary_download_list_has_only_ghostlock(self):
        self.s.a.root_phase='temporary';self.s.a.prepare_only=True;self.s.root_flow()
        self.s.prepare.assert_called_once_with(['ghostlock-karat-v1.0.4.zip']);self.s.connect.assert_not_called()
    def test_google_phase_does_not_unlock_or_backup(self):
        self.s.a.root_phase='google';self.s.permanent_root=Mock();self.s.google_flow=Mock();self.s.root_cleanup=Mock()
        self.s.root_flow();self.s.permanent_root.assert_not_called();self.s.google_flow.assert_called_once();self.s.root_cleanup.assert_called_once_with('google')
    def test_permanent_phase_never_installs_google(self):
        self.s.a.root_phase='permanent';self.s.permanent_root=Mock();self.s.google_flow=Mock();self.s.root_cleanup=Mock()
        self.s.root_flow();self.s.google_flow.assert_not_called();self.s.permanent_root.assert_called_once();self.s.root_cleanup.assert_called_once_with('permanent')
    def test_all_phases_cleanup_in_order(self):
        self.s.a.root_phase='all';order=[]
        self.s.permanent_root=Mock(side_effect=lambda:order.append('permanent'))
        self.s.google_flow=Mock(side_effect=lambda:order.append('google'))
        self.s.root_cleanup=Mock(side_effect=lambda phase:order.append('cleanup-'+phase))
        self.s.root_flow();self.assertEqual(order,['permanent','cleanup-permanent','google','cleanup-google'])
    def test_temporary_cleanup_never_deletes_daemon_or_backups(self):
        self.s.cleanup=Mock();self.s.shell=Mock();self.s.root_cleanup('temporary')
        self.s.cleanup.assert_not_called();self.s.shell.assert_not_called()
    def test_google_cleanup_preserves_backups(self):
        self.s.cleanup=Mock();self.s.shell=Mock();self.s.root_cleanup('google')
        self.s.cleanup.assert_not_called();command=self.s.shell.call_args.args[0]
        self.assertNotIn('/sdcard/TWRP',command);self.assertNotIn('/sdcard/Magisk',command)
    def test_permanent_cleanup_never_removes_google(self):
        self.s.cleanup=Mock();self.s.shell=Mock();self.s.root_cleanup('permanent')
        self.s.cleanup.assert_called_once();self.assertNotIn('/sdcard/google-play',self.s.shell.call_args.args[0])
    def test_backup_stage_skips_existing_checkpoint(self):
        self.s.state['done']=['backup'];fn=Mock();self.s.stage('backup',fn);fn.assert_not_called()
    def test_menu_sorts_and_deduplicates(self):self.assertEqual(menu.selected('5,3,3,1'),['1','3','5'])
    def test_menu_invalid_selection(self):
        with self.assertRaises(ValueError):menu.selected('6')
    def test_menu_failure_stops_next_phase(self):
        with patch.object(sys,'argv',['menu','--steps','2,3','--serial','TEST','--base',self.tmp.name]),patch.object(menu.subprocess,'run',return_value=Mock(returncode=2)) as run,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(menu.main(),2);self.assertEqual(run.call_count,1)
    def test_manual_download_resume_validates_file(self):
        name='amonet-karat-v1.3.0.zip';target=self.s.base/k.payload_path(name)
        self.s.file=Mock(return_value=target)
        def reply(_):target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'mocked archive');return 'RESUME'
        with patch('builtins.input',side_effect=reply),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(self.s.manual_download(name,'403 Forbidden'),target)
        self.assertIn(str(target.parent),output.getvalue());self.assertIn('PLEASE DOWNLOAD THE FILE IN YOUR BROWSER',output.getvalue());self.s.file.assert_called_once_with(name)
    def test_manual_missing_file_keeps_prompt_open(self):
        self.s.file=Mock()
        with patch('builtins.input',side_effect=['RESUME','EXIT']),contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(k.Stop):self.s.manual_download('amonet-karat-v1.3.0.zip','403')
        self.s.file.assert_not_called()
    def test_prepare_does_not_abort_on_http_error(self):
        original=k.Setup.prepare.__get__(self.s);self.s.file=Mock(side_effect=OSError('HTTP 403'));self.s.manual_download=Mock()
        original(['amonet-karat-v1.3.0.zip']);self.s.manual_download.assert_called_once()
    def test_real_config_included(self):
        import json
        config=json.loads((Path(k.__file__).parent.parent/'config/sources.local.json').read_text())
        self.assertEqual(config['amonet-karat-v1.3.0.zip']['url'],k.FILES['amonet-karat-v1.3.0.zip'][0])
if __name__=='__main__':unittest.main()

class BrowserImport(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        args=k.parser().parse_args(['root','--base',self.tmp.name])
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(args)
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close);self.s.log=Mock()
        self.home=Path(self.tmp.name)/'home';self.downloads=self.home/'Downloads';self.downloads.mkdir(parents=True)
    def test_pinned_matching_browser_zip_imported(self):
        import zipfile,hashlib
        name='ghostlock-karat-v1.0.4.zip';candidate=self.downloads/'ghostlock-karat-v1.0.4 (1).zip'
        with zipfile.ZipFile(candidate,'w') as z:z.writestr('data','example')
        digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
        self.s.sources={name:{'sha256':digest}}
        with patch.object(k.Path,'home',return_value=self.home),patch.dict(k.FILES,{name:(k.FILES[name][0],digest)}):self.assertTrue(self.s.import_browser_download(name))
        self.assertEqual(k.sha(self.s.base/k.payload_path(name)),digest)
        self.assertTrue(candidate.exists())
    def test_wrong_hash_download_is_not_imported(self):
        name='ghostlock-karat-v1.0.4.zip';(self.downloads/name).write_bytes(b'wrong')
        with patch.object(k.Path,'home',return_value=self.home):self.assertFalse(self.s.import_browser_download(name))
        self.assertFalse((self.s.base/k.payload_path(name)).exists())
    def test_unrelated_files_not_imported(self):
        (self.downloads/'private.zip').write_bytes(b'private')
        with patch.object(k.Path,'home',return_value=self.home):self.assertFalse(self.s.import_browser_download('ghostlock-karat-v1.0.4.zip'))
