"""Offline progress and microG-launch regression tests."""
import contextlib
import io
import tempfile
import unittest
from unittest.mock import Mock, patch
import downloads
import terminal_ui as ui
import karat as k

class Response(io.BytesIO):
    def __init__(self, data, size=None):
        super().__init__(data);self.headers={} if size is None else {'Content-Length':size}

class ProgressTests(unittest.TestCase):
    def test_known_size_shows_measured_completion_and_copies_bytes(self):
        output=io.BytesIO()
        with contextlib.redirect_stdout(io.StringIO()) as console:
            self.assertEqual(downloads.copy_with_progress(Response(b'a'*300000,'300000'),output,'microg.apk'),300000)
        self.assertEqual(output.getvalue(),b'a'*300000)
        self.assertIn('100.0%',console.getvalue());self.assertIn('MiB/s',console.getvalue())
    def test_unknown_length_does_not_invent_percentage(self):
        with contextlib.redirect_stdout(io.StringIO()) as console:
            downloads.copy_with_progress(Response(b'bytes'),io.BytesIO(),'file')
        self.assertIn('MiB',console.getvalue());self.assertNotIn('%',console.getvalue())
    def test_truncated_transfer_is_rejected(self):
        with contextlib.redirect_stdout(io.StringIO()) as console:
            with self.assertRaises(OSError): downloads.copy_with_progress(Response(b'few','100'),io.BytesIO(),'file')
        self.assertNotIn('100.0%',console.getvalue())
    def test_bad_length_header_uses_indeterminate_progress(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(downloads.copy_with_progress(Response(b'ok','invalid'),io.BytesIO(),'file'),2)
    def test_activity_bar_is_indeterminate_and_closes_cleanly(self):
        stream=io.StringIO();stream.isatty=lambda:True
        clock=Mock(side_effect=[0,0,1])
        bar=ui.Progress('Installing',stream=stream,clock=clock);bar.update();bar.close()
        self.assertIn('[===',stream.getvalue());self.assertNotIn('%',stream.getvalue());self.assertTrue(bar.closed)
    def test_redirected_output_is_throttled(self):
        stream=io.StringIO();clock=Mock(side_effect=[0,0,0.1,1,4])
        bar=ui.Progress('file',stream=stream,clock=clock);bar.update(1);bar.update(2);bar.update(3);bar.close()
        self.assertEqual(len(stream.getvalue().splitlines()),2)

class MicrogLaunch(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['root','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close);self.s.log=Mock()
    def test_resolved_activity_is_launched(self):
        self.s.shell=Mock(side_effect=['com.google.android.gms/org.microg.gms.ui.SettingsActivity','No activity found','Starting: Intent {}\nStatus: ok'])
        self.s.open_microg_settings()
        self.assertIn('am start -W -n com.google.android.gms/org.microg.gms.ui.SettingsActivity',self.s.shell.call_args.args[0])
        self.assertIn('OK:',self.s.log.call_args.args[0])
    def test_missing_launcher_uses_settings_component(self):
        self.s.shell=Mock(side_effect=['No activity found','No activity found','Status: ok'])
        self.s.open_microg_settings();self.assertIn('OK:',self.s.log.call_args.args[0])
    def test_launch_error_shows_manual_guidance(self):
        self.s.shell=Mock(side_effect=['No activity found','No activity found','Starting: Intent {}\nError type 3'])
        self.s.open_microg_settings();self.assertTrue(self.s.log.call_args.args[0].startswith('WARNING:'))
    def test_install_process_gets_activity_bar(self):
        import sys
        # Exercise the real streaming subprocess loop, without ADB or a device.
        real=k.subprocess.Popen
        def spawn(*args,**kwargs):return real([sys.executable,'-c','print("Success")'],**kwargs)
        bar=Mock()
        with patch.object(k.subprocess,'Popen',side_effect=spawn),patch.object(k.ui,'Progress',return_value=bar) as factory,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.s.run(['adb','-s','TEST','install','-r','file.apk']),'Success')
        factory.assert_called_once();bar.update.assert_called();bar.close.assert_called_once()

    def test_selfcheck_opens_before_prompt(self):
        self.s.state={'done':['framework','fakegapps-scope'],'pending':None}
        self.s.stage=Mock();self.s.finish=Mock();events=[]
        self.s.open_microg_settings=Mock(side_effect=lambda:events.append('open'))
        self.s.pause=Mock(side_effect=lambda *args:events.append('prompt'))
        self.s.ensure_preinit=Mock();self.s.verify_vector_policy=Mock()
        self.s.google_flow();self.assertEqual(events,['open','prompt'])
