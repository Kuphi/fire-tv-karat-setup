"""Main launcher resumes the saved plan without separate repair commands."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import setup_menu as menu

class MainResume(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.work=self.base/'karat-automation/runtime'
        self.work.mkdir(parents=True)
    def state(self,pending='postota',serial='TEST'):
        p=self.work/'TEST.json';p.write_text(json.dumps({'serial':serial,'done':['unlock','backup'],'pending':pending}))
        return p
    def run_menu(self,extra,results):
        with patch('sys.argv',['menu','--base',str(self.base),'--serial','TEST',*extra]), \
             patch.object(menu.subprocess,'run',side_effect=[Mock(returncode=n) for n in results]) as run, \
             patch('builtins.input',side_effect=AssertionError('resume must not request phase selection')), \
             contextlib.redirect_stdout(io.StringIO()):
            code=menu.main()
        return code,run.call_args_list
    def test_usb_detection_resumes_without_menu_selection(self):
        self.state()
        with patch('sys.argv',['menu','--base',str(self.base)]), \
             patch.object(menu.subprocess,'run',side_effect=[Mock(returncode=0,stdout='TEST\n'),Mock(returncode=2)]) as run, \
             patch('builtins.input',side_effect=AssertionError('no phase selection during resume')), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(menu.main(),2)
        self.assertEqual(run.call_args_list[0].args[0],['adb','-d','get-serialno'])
        command=run.call_args_list[1].args[0]
        self.assertEqual(command[command.index('--root-phase')+1],'permanent')
        self.assertEqual(command[command.index('--serial')+1],'TEST')
    def test_legacy_postota_checkpoint_resumes_phase_two(self):
        p=self.state();before=p.read_bytes()
        code,calls=self.run_menu([], [2]);self.assertEqual(code,2)
        self.assertEqual(calls[0].args[0][calls[0].args[0].index('--root-phase')+1],'permanent')
        self.assertEqual(p.read_bytes(),before)
    def test_failed_phase_keeps_rest_of_selected_plan(self):
        code,calls=self.run_menu(['--steps','1 2 3'],[0,2]);self.assertEqual(code,2)
        saved=json.loads((self.work/'TEST.setup-plan.json').read_text())
        self.assertEqual(saved['remaining'],['2','3'])
        code,calls=self.run_menu([], [0,0]);self.assertEqual(code,0)
        self.assertEqual(calls[0].args[0][calls[0].args[0].index('--root-phase')+1],'permanent')
        self.assertEqual(calls[1].args[0][calls[1].args[0].index('--root-phase')+1],'google')
        self.assertEqual(json.loads((self.work/'TEST.setup-plan.json').read_text())['remaining'],[])
    def test_app_selection_survives_failed_main_run(self):
        self.run_menu(['--steps','5','--apps','1 6'],[2])
        code,calls=self.run_menu([], [0]);self.assertEqual(code,0)
        self.assertEqual(calls[0].args[0][-2:],['--apps','1 6'])
    def test_other_device_checkpoint_is_not_adopted(self):
        self.state(serial='OTHER')
        code,calls=self.run_menu([], []);self.assertEqual(code,2);self.assertEqual(calls,[])
    def test_malformed_plan_is_not_adopted(self):
        (self.work/'TEST.setup-plan.json').write_text('{bad json')
        code,calls=self.run_menu([], []);self.assertEqual(code,2);self.assertEqual(calls,[])
    def test_preview_never_reads_or_writes_runtime_plan(self):
        (self.work/'TEST.setup-plan.json').write_text('{bad json')
        before=list(self.work.iterdir())
        code,calls=self.run_menu(['--preview-only','--steps','2'],[0])
        self.assertEqual(code,0);self.assertEqual(list(self.work.iterdir()),before)
    def test_old_completed_root_resumes_new_reboot(self):
        p=self.state(pending=None);state=json.loads(p.read_text())
        state['done'].extend(['magisk-ui','permanent-cleanup']);p.write_text(json.dumps(state))
        self.assertEqual(menu.resume_choice(self.base,'TEST')[0],['2'])
    def test_completed_root_checkpoint_does_not_infer_repeat(self):
        self.state(pending=None)
        p=self.work/'TEST.json';state=json.loads(p.read_text());state['done'].extend(['permanent-cleanup','magisk-setup-boot']);p.write_text(json.dumps(state))
        self.assertEqual(menu.resume_choice(self.base,'TEST')[0],[])
if __name__=='__main__':unittest.main()
