import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import karat as k
import terminal_ui as ui

class TerminalUI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        args=k.parser().parse_args(['root','--base',self.tmp.name])
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(args)
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
    def test_technical_output_hidden_but_kept_in_full_log(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:self.s.log('application-label-af: Magisk',detail=True)
        self.assertEqual(out.getvalue(),'')
        self.assertIn('application-label-af: Magisk',Path(self.s.logfile.name).read_text())
    def test_verbose_shows_technical_output(self):
        self.s.a.verbose=True
        with contextlib.redirect_stdout(io.StringIO()) as out:self.s.log('technical-command-output',detail=True)
        self.assertIn('technical-command-output',out.getvalue())
    def test_file_status_hides_long_hash(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:self.s.log('FILE: Magisk-v30.7.apk; SHA256=secret-long-hash; already available; not downloading again')
        self.assertIn('Magisk-v30.7.apk',out.getvalue());self.assertIn('verified',out.getvalue())
        self.assertNotIn('secret-long-hash',out.getvalue())
    def test_input_card_has_choices(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:ui.action('Please confirm on the TV.')
        text=out.getvalue();self.assertIn('YOUR INPUT',text);self.assertIn('RESUME',text);self.assertIn('EXIT',text)
    def test_no_ansi_when_redirected(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:ui.title('Title');ui.event('OK: backup')
        self.assertNotIn('\x1b[',out.getvalue());self.assertIn('One-time backup',out.getvalue())
    def test_blank_confirmation_keeps_prompt_open(self):
        with patch('builtins.input',side_effect=['','wrong','ROOT']) as prompt,contextlib.redirect_stdout(io.StringIO()):self.s.confirm('ROOT','Test')
        self.assertEqual(prompt.call_count,3)
    def test_exit_confirmation_stops_without_starting(self):
        with patch('builtins.input',return_value='EXIT'),contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(k.Stop):self.s.confirm('UNLOCK','Test')
    def test_apps_preview_does_not_claim_none_missing(self):
        import dry_run
        with contextlib.redirect_stdout(io.StringIO()) as out:dry_run.preview('apps')
        self.assertNotIn('MISSING APPS: none',out.getvalue())
        self.assertIn('not actually performed',out.getvalue())
if __name__=='__main__':unittest.main()
