"""Focused regression checks for the shared Linux/Windows bundle; no devices."""
import ast
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import karat as k
import install_apps_and_optimize as apps

class Bundle(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        args=k.parser().parse_args(['root','--base',self.tmp.name])
        with contextlib.redirect_stdout(io.StringIO()): self.s=k.Setup(args)
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.state={'serial':'TEST','done':[],'pending':None}
        self.s.statefile=self.s.work/'TEST.json';self.s.log=Mock()

    def test_all_three_models_with_exact_profile(self):
        for model in ('AFTKRT','AFTKM','AFTMA08C15'):
            self.s.state.pop('profile',None)
            properties={'ro.product.device':'karat','ro.product.model':model,'ro.build.fingerprint':'Amazon/karat/karat:11/RS8160.3380N/0030501844100:user/amz-p,release-keys','ro.build.version.incremental':'0030501844100'}
            self.s.prop=Mock(side_effect=lambda key:properties.get(key,''))
            self.s.shell=Mock(return_value='Linux 5.10.43-android12-9-ga8c852b26125 armv8l')
            self.s.identity()

    def test_verifier_exact_receiver_success(self):
        self.s.shell=Mock(side_effect=['Component new state: disabled','1 receivers found:\ncom.amazon.adep/.nimh.receiver.PackageVerificationReceiver'])
        self.s.verifier()
    def test_eleven_receivers_not_mistaken_for_one(self):
        self.s.shell=Mock(side_effect=['new state: disabled','11 receivers found:\ncom.amazon.adep/.nimh.receiver.PackageVerificationReceiver'])
        with self.assertRaises(k.Stop):self.s.verifier()
    def test_wrong_amazon_component_rejected(self):
        self.s.shell=Mock(side_effect=['new state: disabled','1 receivers found:\ncom.amazon.adep/Other'])
        with self.assertRaises(k.Stop):self.s.verifier()
    def test_failed_disable_never_queries(self):
        self.s.shell=Mock(return_value='Error type 3')
        with self.assertRaises(k.Stop):self.s.verifier()
        self.assertEqual(self.s.shell.call_count,1)
    def test_reboot_order(self):
        order=[];self.s.verifier=Mock(side_effect=lambda:order.append('verify'));self.s.reboot=Mock(side_effect=lambda:order.append('reboot'))
        self.s.microg_reboot();self.assertEqual(order,['verify','reboot','verify'])
    def test_bad_verifier_blocks_reboot(self):
        self.s.verifier=Mock(side_effect=k.Stop('two verifiers'));self.s.reboot=Mock()
        with self.assertRaises(k.Stop):self.s.microg_reboot()
        self.s.reboot.assert_not_called()
    def test_bad_postboot_check_not_checkpointed(self):
        self.s.verifier=Mock(side_effect=[None,k.Stop('two verifiers')]);self.s.reboot=Mock()
        with self.assertRaises(k.Stop):self.s.stage('microg-boot',self.s.microg_reboot)
        self.assertNotIn('microg-boot',self.s.state['done'])
    def test_google_install_and_promotion_have_guard(self):
        tree=ast.parse(Path(k.__file__).read_text())
        root=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='google_flow')
        def body(name):
            return next(n.args[1].body for n in ast.walk(root) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='stage' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value==name)
        self.assertEqual([n.func.attr for n in body('google-apks').elts],['install','install','verifier'])
        self.assertEqual([n.func.attr for n in body('microg-promotion').elts],['verifier','module'])
    def test_cleanup_only_after_verified_backup(self):
        self.s.cleanup=Mock(side_effect=k.Stop('missing backup'));self.s.shell=Mock()
        with self.assertRaises(k.Stop):self.s.root_cleanup()
        self.s.shell.assert_not_called()
    def test_cleanup_no_blanket_twrp_delete(self):
        self.s.cleanup=Mock();self.s.shell=Mock();self.s.root_cleanup()
        command=self.s.shell.call_args.args[0]
        self.assertNotIn('rm -rf /sdcard/TWRP',command)
        self.assertIn('rmdir',command)
        self.assertIn('/sdcard/google-play/vector.zip',command)
    def test_apps_has_no_cleanup(self):
        tree=ast.parse(Path(apps.__file__).read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
                self.assertNotIn(n.func.attr,('cleanup','root_cleanup'))
        self.assertNotIn('rm -rf',Path(apps.__file__).read_text())
    def test_boot_help_has_manual_repair_and_keeps_checkpoints(self):
        self.s.boot_help();text='\n'.join(c.args[0] for c in self.s.log.call_args_list)
        self.assertIn('--repair-verifier',text);self.assertIn('Preserve checkpoints',text)
    def test_repair_order_and_checkpoint(self):
        order=[];self.s.connect=Mock();self.s.root_ok=Mock()
        self.s.shell=Mock(side_effect=lambda cmd: order.append(cmd) or 'OK')
        self.s.reboot=Mock(side_effect=lambda:order.append('reboot'))
        self.s.verifier=Mock(side_effect=lambda:order.append('verify'))
        self.s.verifier_repair()
        self.assertEqual(order[2:5],['reboot','verify','rm /data/adb/modules/microg_installer_revived_again/disable && sync'])
        self.assertEqual(order[-2:],['reboot','verify'])
        self.assertIn('microg-boot',self.s.state['done'])
    def test_repair_blocks_unknown_pending(self):
        self.s.connect=Mock();self.s.state['pending']='unlock';self.s.shell=Mock()
        with self.assertRaises(k.Stop):self.s.verifier_repair()
        self.s.shell.assert_not_called()
    def test_reader_handles_timeout(self):
        with self.assertRaises(k.Stop):self.s.run([sys.executable,'-c','import time;time.sleep(2)'],timeout=0.1)
    def test_windows_pipe_output_branch(self):
        with patch.object(k.os,'name','nt'):
            self.assertEqual(self.s.run([sys.executable,'-c','print("pipe")']),'pipe')
    def test_windows_atomic_save_without_directory_fsync(self):
        path=Path(self.tmp.name)/'windows.json'
        with patch.object(k.os,'name','nt'):k.atomic_json(path,{'ok':True})
        self.assertEqual(json.loads(path.read_text()),{'ok':True})
    def test_launcher_listing(self):
        base=Path(k.__file__).parent.parent
        names=['00_setup','01_temporary_root_and_disable_ota','02_permanent_root_magisk','03_google_play_and_microg','04_emotn-launcher-setup','05_install_apps_and_optimize']
        self.assertEqual(sorted(p.stem for p in base.glob('*.sh')),names)
        for name in names:
            self.assertTrue((base/(name+'.ps1')).is_file());self.assertTrue((base/(name+'.bat')).is_file())
    def test_shared_package_no_personal_runtime(self):
        base=Path(k.__file__).parent.parent
        self.assertFalse((base/'karat-automation/runtime').exists())
        self.assertFalse((base/'karat-automation/Archiv').exists())

if __name__=='__main__':unittest.main()
