"""Offline tests: no real adb and no network downloads."""
import contextlib
import importlib.util
import io
import json
import shutil
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import Mock, patch
import zipfile

spec = importlib.util.spec_from_file_location('karat', Path(__file__).with_name('karat.py'))
k = importlib.util.module_from_spec(spec); spec.loader.exec_module(k)

class Safety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        args = k.parser().parse_args(['root','--base',self.tmp.name])
        with contextlib.redirect_stdout(io.StringIO()): self.s = k.Setup(args)
        self.addCleanup(self.s.lock.close)
        self.addCleanup(self.s.logfile.close)
        self.s.log = Mock()
        self.s.recovery_ready = Mock()
        self.s.serial = 'TEST'
        self.s.statefile = self.s.work/'TEST.json'
        self.s.state = {'serial':'TEST','done':[],'pending':None}
        self.s.backup = self.s.base/'backups'/'TEST'/'automation-before-root'

    def test_unknown_write_never_retries(self):
        self.s.state['pending'] = 'postota'
        fn = Mock()
        with self.assertRaises(k.Stop): self.s.stage('postota',fn,risky=True)
        fn.assert_not_called()

    def test_failed_write_persists_pending(self):
        with self.assertRaises(k.Stop):
            self.s.stage('postota',Mock(side_effect=k.Stop('bad')),risky=True)
        self.assertEqual(json.loads(self.s.statefile.read_text())['pending'],'postota')

    def test_completed_stage_not_repeated(self):
        fn = Mock()
        self.s.stage('postota',fn,risky=True)
        self.s.stage('postota',fn,risky=True)
        fn.assert_called_once()

    def test_wrong_model_rejected(self):
        self.s.prop = Mock(side_effect=lambda p: {'ro.product.device':'kara'}.get(p,''))
        with self.assertRaises(k.Stop): self.s.identity()

    def test_wrong_build_rejected(self):
        self.s.prop = Mock(side_effect=lambda p: {'ro.product.device':'karat','ro.product.model':'AFTKRT','ro.build.fingerprint':'other'}.get(p,''))
        with self.assertRaises(k.Stop): self.s.identity()

    def test_unknown_recovery_not_adopted(self):
        self.s.prop = Mock(side_effect=lambda p: {'ro.product.device':'karat','ro.twrp.version':'3.7.1_12-0'}.get(p,''))
        with self.assertRaises(k.Stop): self.s.identity()

    def test_existing_download_is_never_requested(self):
        path = self.s.base/'google-play/fakegapps.apk'; path.parent.mkdir()
        with zipfile.ZipFile(path,'w') as z: z.writestr('AndroidManifest.xml','test')
        self.s.apk_metadata = Mock()
        with patch.object(k.urllib.request,'urlopen') as net:
            self.assertEqual(self.s.file('google-play/fakegapps.apk'),path)
            net.assert_not_called()

    def test_pinned_hash_mismatch_rejected(self):
        path = self.s.base/'amonet-karat-v1.3.0.zip'
        with zipfile.ZipFile(path,'w') as z: z.writestr('a','bad')
        with self.assertRaises(k.Stop): self.s.file(path.name)
        self.assertTrue(path.exists())

    def test_zip_traversal_rejected(self):
        path = self.s.base/'evil.zip'
        with zipfile.ZipFile(path,'w') as z: z.writestr('../escape','bad')
        with self.assertRaises(k.Stop): k.archive_ok(path)

    def test_flash_exit_zero_without_marker_rejected(self):
        self.s.prop = Mock(return_value='3.7.1_12-0')
        self.s.file = Mock(return_value=Path('/not/read'))
        self.s.push = Mock()
        self.s.shell = Mock(return_value='Done processing script file')
        with self.assertRaises(k.Stop): self.s.flash('post-ota-karat-v1.0.0.zip','- info done')

    def test_flash_error_despite_done_rejected(self):
        self.s.prop = Mock(return_value='3.7.1_12-0')
        self.s.file = Mock(return_value=Path('/not/read'))
        self.s.push = Mock()
        self.s.shell = Mock(return_value='ERROR patching\n- info done')
        with self.assertRaises(k.Stop): self.s.flash('post-ota-karat-v1.0.0.zip','- info done')

    def test_magisk_uses_zip_remote_filename(self):
        self.s.prop = Mock(return_value='3.7.1_12-0')
        self.s.file = Mock(return_value=Path('/not/read'))
        self.s.push = Mock()
        self.s.shell = Mock(return_value='Magisk 30.7\n- Done')
        self.s.flash('Magisk-v30.7.apk','- Done')
        self.assertEqual(self.s.push.call_args.args[1],'/sdcard/Magisk-v30.7.zip')

    def test_postota_wrong_bytes_no_flash_and_unmounts(self):
        self.s.verify_backups = Mock()
        self.s.backup.mkdir(parents=True)
        (self.s.backup/'verified.json').write_text('{}')
        self.s.shell = Mock(side_effect=['','','ff',''])
        self.s.flash = Mock()
        with self.assertRaises(k.Stop): self.s.postota()
        self.s.flash.assert_not_called()
        self.s.shell.assert_called_with('umount /mnt/postota-check')

    def test_transfer_hash_mismatch_blocks_use(self):
        path = self.s.base/'bytes'; path.write_bytes(b'payload')
        self.s.adb = Mock()
        self.s.shell = Mock(return_value='wrong /sdcard/file')
        with self.assertRaises(k.Stop): self.s.push(path,'/sdcard/file')

    def test_host_failure_is_not_success(self):
        with self.assertRaises(k.Stop): self.s.run([k.sys.executable,'-c','print("failure");raise SystemExit(7)'])

    def test_process_output_is_captured(self):
        out = self.s.run([k.sys.executable,'-c','print("visible output")'])
        self.assertEqual(out,'visible output')

    def test_active_existing_root_may_probe_recovery(self):
        self.s.verifying_existing = True
        self.s.state['profile'] = {'build':'RS8185.3879N','incremental':'0033018554244','kernel_suffix':'-g8b4baa819147'}
        self.s.prop = Mock(side_effect=lambda p: {'ro.product.device':'karat','ro.twrp.version':'3.7.1_12-0'}.get(p,''))
        self.s.identity()

    def profile_device(self, build, incremental, suffix, reported_incremental=None):
        fp = f'Amazon/karat/karat:11/{build}/{incremental}:user/amz-p,release-keys'
        properties = {'ro.product.device':'karat','ro.product.model':'AFTKRT','ro.build.fingerprint':fp,
                      'ro.build.version.incremental':reported_incremental or incremental}
        self.s.prop = Mock(side_effect=lambda p: properties.get(p,''))
        self.s.shell = Mock(return_value=f'Linux localhost 5.10.43-android12-9{suffix} #1 SMP armv8l')

    def test_all_fifteen_exact_profiles_allowed(self):
        self.assertEqual(len(k.SUPPORTED),15)
        for (build, incremental), (version, suffix) in k.SUPPORTED.items():
            with self.subTest(build=build):
                self.s.state.pop('profile',None)
                self.profile_device(build,incremental,suffix)
                self.s.identity()
                self.assertEqual(self.s.state['profile']['fire_os'],version)

    def test_our_previous_unlisted_build_is_excluded(self):
        self.profile_device('RS8185.3885N','0033018555780','-g8b4baa819147')
        with self.assertRaises(k.Stop): self.s.identity()

    def test_mixing_listed_build_and_incremental_is_rejected(self):
        self.profile_device('RS8185.3879N','0032548774788','-g8b4baa819147')
        with self.assertRaises(k.Stop): self.s.identity()

    def test_listed_kernel_from_other_profile_is_rejected(self):
        self.profile_device('RS8185.3879N','0033018554244','-g76bdd754c12c')
        with self.assertRaises(k.Stop): self.s.identity()

    def test_incremental_property_must_match_fingerprint(self):
        self.profile_device('RS8185.3879N','0033018554244','-g8b4baa819147','0032548774788')
        with self.assertRaises(k.Stop): self.s.identity()

    def test_checkpoint_cannot_migrate_to_another_allowed_build(self):
        self.profile_device('RS8185.3879N','0033018554244','-g8b4baa819147')
        self.s.identity()
        self.profile_device('RS8182.3811N','0032548774788','-g76bdd754c12c')
        with self.assertRaises(k.Stop): self.s.identity()

    def test_recovery_requires_previously_allowed_profile(self):
        self.s.state['done'] = ['unlock']
        self.s.state['profile'] = {'build':'RS8185.3885N','incremental':'0033018555780','kernel_suffix':'-g8b4baa819147'}
        self.s.prop = Mock(side_effect=lambda p: {'ro.product.device':'karat','ro.twrp.version':'3.7.1_12-0'}.get(p,''))
        with self.assertRaises(k.Stop): self.s.identity()

    def test_old_unbound_checkpoint_is_not_reused(self):
        self.s.state['done'] = ['unlock']
        self.profile_device('RS8185.3879N','0033018554244','-g8b4baa819147')
        with self.assertRaises(k.Stop): self.s.identity()

    def test_default_file_folder_is_bundle_parent(self):
        args = k.parser().parse_args(['root'])
        self.assertEqual(Path(args.base),k.HERE.parent)

    @unittest.skipIf(k.os.name == 'nt' or shutil.which('bash') is None, 'Bash-Starter nur unter Linux testen')
    def test_main_folder_launchers_find_base_from_other_working_directory(self):
        bundle = Path(__file__).resolve().parent.parent
        target = Path(self.tmp.name)/'Ordner mit Leerzeichen'/'Fire TV karat'
        target.mkdir(parents=True)
        engine = target/'karat-automation'; engine.mkdir()
        (engine/'karat.py').write_text('import sys,json;print(json.dumps(sys.argv[1:]))')
        import shutil
        shutil.copytree(bundle/'tools',target/'tools')
        for filename,flow in [('02_permanent_root_magisk.sh','root'),('04_emotn-launcher-setup.sh','emotn')]:
            with self.subTest(flow=flow):
                (target/filename).write_text((bundle/filename).read_text())
                out = subprocess.check_output(['bash',str(target/filename),'--prepare-only'],cwd='/',text=True)
                expected=[flow,'--base',str(target)]+(['--root-phase','permanent'] if flow=='root' else [])+['--prepare-only']
                self.assertEqual(json.loads(out),expected)

    @unittest.skipIf(k.os.name == 'nt' or shutil.which('bash') is None, 'Bash-Starter nur unter Linux testen')
    def test_main_folder_launchers_explain_missing_engine(self):
        bundle = Path(__file__).resolve().parent.parent
        target = Path(self.tmp.name)/'incomplete';target.mkdir()
        import shutil
        shutil.copytree(bundle/'tools',target/'tools')
        script = target/'02_permanent_root_magisk.sh';script.write_text((bundle/'02_permanent_root_magisk.sh').read_text())
        result = subprocess.run(['bash',str(script),'--prepare-only'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('complete package',result.stderr)

    def test_sorted_existing_download_is_reused(self):
        path=self.s.base/k.payload_path('google-play/fakegapps.apk');path.parent.mkdir(parents=True)
        with zipfile.ZipFile(path,'w') as z:z.writestr('AndroidManifest.xml','test')
        self.s.apk_metadata=Mock()
        with patch.object(k.urllib.request,'urlopen') as network:
            self.assertEqual(self.s.file('google-play/fakegapps.apk'),path)
            network.assert_not_called()

    def test_verifier_conflict_blocks_promotion(self):
        self.s.shell = Mock(side_effect=['new state: disabled','2 receivers found: com.amazon.adep/X com.android.vending/Y'])
        with self.assertRaises(k.Stop): self.s.verifier()

    def test_cleanup_refuses_missing_pc_backup(self):
        self.s.backup.mkdir(parents=True)
        k.atomic_json(self.s.backup/'verified.json',{'serial':'TEST','files':{'absent':'abc'}})
        self.s.shell = Mock()
        with self.assertRaises(k.Stop): self.s.cleanup()
        self.s.shell.assert_not_called()

    def test_manual_scope_gate_cannot_silently_pass(self):
        with self.assertRaises(k.Stop): self.s.pause('fakegapps_ready','scope')

if __name__ == '__main__': unittest.main()
