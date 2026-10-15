import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import karat
import install_apps_and_optimize as apps
import dry_run

class DryRun(unittest.TestCase):
    def test_root_without_setup_or_device_or_network(self):
        with patch.object(sys,'argv',['karat.py','root','--preview-only']),patch.object(karat,'Setup') as setup,patch.object(karat.subprocess,'Popen') as process,patch.object(karat.urllib.request,'urlopen') as net,contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(karat.main(),0)
            setup.assert_not_called();process.assert_not_called();net.assert_not_called()
            self.assertIn('Simulated data',out.getvalue())
    def test_emotn_preview(self):
        with patch.object(sys,'argv',['karat.py','emotn','--preview-only']),patch.object(karat,'Setup') as setup,contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(karat.main(),0);setup.assert_not_called()
            self.assertIn('your own town',out.getvalue())
    def test_apps_without_setup(self):
        with patch.object(sys,'argv',['apps.py','--preview-only']),patch.object(apps,'Apps') as engine,contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(apps.main(),0);engine.assert_not_called()
            self.assertIn('Netflix',out.getvalue())
    def test_timeout_has_repair_not_success(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:dry_run.preview('root','boot-timeout')
        text=out.getvalue();self.assertIn('BOOT HELP',text);self.assertIn('--repair-verifier',text)
        self.assertNotIn('OK: microg-boot',text);self.assertNotIn('START: root-cleanup',text)
    def test_windows_skips_dependency_install_in_preview(self):
        content=(Path(karat.__file__).parent.parent/'tools/launch.ps1').read_text()
        self.assertIn("$ForwardArgs -notcontains '--preview-only'",content)
if __name__=='__main__':unittest.main()

class DownloadDryRun(unittest.TestCase):
    def test_default_links_in_engine(self):
        for name in ('amonet-karat-v1.3.0.zip','ghostlock-karat-v1.0.4.zip','post-ota-karat-v1.0.0.zip'):
            self.assertTrue(karat.FILES[name][0].startswith('https://xdaforums.com/attachments/'))
        self.assertTrue(karat.FILES['google-play/play-store-tv.apk'][0].startswith('https://www.apkmirror.com/'))
    def test_empty_override_uses_default_download(self):
        import tempfile,zipfile
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as tmp:
            args=karat.parser().parse_args(['root','--base',tmp])
            with contextlib.redirect_stdout(io.StringIO()):e=karat.Setup(args)
            try:
                e.sources={'google-play/fakegapps.apk':{'url':''}};e.apk_metadata=Mock();e.log=Mock()
                payload=io.BytesIO()
                with zipfile.ZipFile(payload,'w') as z:z.writestr('AndroidManifest.xml','demo')
                class Response(io.BytesIO):
                    def geturl(self):return 'https://github.com/whew-inc/FakeGApps/releases/download/6.6/app-release.apk'
                with patch.object(karat.urllib.request,'urlopen',return_value=Response(payload.getvalue())) as net:
                    self.assertTrue(e.file('google-play/fakegapps.apk').is_file())
                    self.assertEqual(net.call_args.args[0].full_url,'https://github.com/whew-inc/FakeGApps/releases/download/6.6/app-release.apk')
            finally:e.logfile.close();e.lock.close()
    def test_root_download_dry_run_never_connects(self):
        import tempfile
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as tmp:
            args=karat.parser().parse_args(['root','--base',tmp])
            with contextlib.redirect_stdout(io.StringIO()):e=karat.Setup(args)
            e.prepare=Mock();e.connect=Mock();e.log=Mock()
            def factory(actual):e.a=actual;return e
            with patch.object(sys,'argv',['karat.py','root','--base',tmp,'--dry-run']),patch.object(karat,'Setup',side_effect=factory),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(karat.main(),0)
            self.assertTrue(e.a.prepare_only);e.prepare.assert_called_once();e.connect.assert_not_called()
