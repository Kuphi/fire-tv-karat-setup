"""Language selection and localized-engine regressions, without device access."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import bilingual

class Bilingual(unittest.TestCase):
    def test_explicit_language_overrides_environment(self):
        with patch.dict(os.environ,{'FIRE_TV_LANG':'de'}):
            self.assertEqual(bilingual.select_language(['--steps','2','--lang','en']),('en',['--steps','2']))
    def test_equals_form(self):
        self.assertEqual(bilingual.select_language(['--lang=de','--preview-only']),('de',['--preview-only']))
    def test_noninteractive_defaults_to_english(self):
        with patch.dict(os.environ,{},clear=True),patch('sys.stdin.isatty',return_value=False):
            self.assertEqual(bilingual.select_language([]),('en',[]))
    def test_interactive_language_choice(self):
        with patch.dict(os.environ,{},clear=True),patch('sys.stdin.isatty',return_value=True),patch('builtins.input',side_effect=['','2']) as reply,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bilingual.select_language([]),('de',[]));self.assertEqual(reply.call_count,2)
    def test_exit_does_not_start_setup(self):
        with patch.dict(os.environ,{},clear=True),patch('sys.stdin.isatty',return_value=True),patch('builtins.input',return_value='EXIT'),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bilingual.select_language([]),(None,[]))
    def test_invalid_language_rejected(self):
        with self.assertRaises(ValueError):bilingual.select_language(['--lang','fr'])
    def test_missing_language_value_rejected(self):
        with self.assertRaises(ValueError):bilingual.select_language(['--lang'])
    def preview(self,lang):
        base=Path(__file__).resolve().parent.parent
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,str(base/'karat-automation/setup_menu.py'),'--lang',lang,'--preview-only','--steps','2,3,5','--apps','1 2 6'],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        return result.stdout
    def test_english_preview(self):
        text=self.preview('en');self.assertIn('STEP 1 OF 3',text);self.assertIn('Temporary',text)
        self.assertIn('Selected apps: Netflix, YouTube, CX File Explorer',text)
    def test_german_preview_and_children_keep_choice(self):
        text=self.preview('de');self.assertIn('SCHRITT 1 VON 3',text);self.assertIn('Temporäres',text)
        self.assertIn('Ausgewählte Apps: Netflix, YouTube, CX File Explorer',text)
        self.assertNotIn('Choose language',text)
    def test_german_help_includes_language_option(self):
        path=Path(__file__).parent/'karat.py'
        result=subprocess.run([sys.executable,str(path),'root','--lang','de','--help'],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('--lang',result.stdout)
        self.assertIn('Verwendung:',result.stdout)
    def test_german_engine_retains_safety_tests(self):
        import test_safety
        table=json.loads((Path(__file__).parent/'locales/de.json').read_text())['karat']
        spec=importlib.util.spec_from_file_location('localized_karat',Path(__file__).parent/'karat.py',loader=bilingual.LocalizedLoader('karat',table))
        engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(test_safety.Safety)
        with patch.object(test_safety,'k',engine),contextlib.redirect_stdout(io.StringIO()):
            result=unittest.TestResult();suite.run(result)
        self.assertTrue(result.wasSuccessful(),str(result.errors)+str(result.failures))
if __name__=='__main__':unittest.main()
