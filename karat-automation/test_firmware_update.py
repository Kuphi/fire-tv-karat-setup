"""Offline update transactions, checkpoint boundaries and boot gates."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile
import karat as k
import setup_menu as menu
from firmware_update import FINGERPRINT, PREFIX, FIRMWARE

SOURCE={'build':'RS8158.4105N','incremental':'0030468475268','fire_os':'8.1.5.8','kernel_suffix':'-gb7ca23cc70e6','fingerprint':'Amazon/karat/karat:11/RS8158.4105N/0030468475268:user/amz-p,release-keys'}
TARGET={'build':'RS8182.3811N','incremental':'0032548774788','fire_os':'8.1.8.2','kernel_suffix':'-g76bdd754c12c','fingerprint':FINGERPRINT}
class Update(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['root','--root-phase','update','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.statefile=self.s.work/'TEST.json'
        self.s.state={'serial':'TEST','done':[],'pending':None,'profile':copy.deepcopy(SOURCE)}
        self.s.log=Mock();self.s.confirm=Mock();self.s.root_ok=Mock();self.s.require_preinit=Mock()
        self.events=[];self.recovery=False
        self.s.prop=Mock(side_effect=lambda key:('3.7.1_12-0' if self.recovery else '') if key=='ro.twrp.version' else '1')
        self.s.shell=Mock(side_effect=lambda cmd,**kw: '30.7:MAGISK:R' if cmd=='magisk -v' else 'MODULE_ENABLED' if 'echo MODULE_ENABLED' in cmd else '')
        def reboot(recovery=False):
            self.events.append('recovery' if recovery else 'boot');self.recovery=recovery
            if not recovery and PREFIX+'firmware' in self.s.state['done']:self.s.state['profile']=copy.deepcopy(TARGET)
        self.s.reboot=Mock(side_effect=reboot)
        for method in ('recovery_ready','backups','verify_backups','cleanup','postota','magisk_app','magisk_setup_reboot','ensure_preinit','verify_vector_policy','restore_wifi','root_cleanup'):
            setattr(self.s,method,Mock(side_effect=lambda *args,m=method:self.events.append(m)))
        self.s.update_modules_off=Mock(side_effect=lambda:self.s.state['firmware_update'].update(restore_modules=[]))
        self.s.update_firmware_flash=Mock(side_effect=lambda:self.events.append('firmware'))
        self.s.flash=Mock(side_effect=lambda *args:self.events.append('magisk-flash'))
    def tx(self):
        self.s.state['firmware_update']={'target':FINGERPRINT,'source_profile':copy.deepcopy(SOURCE),'restore_modules':[]}
    def test_all_and_all_u_order(self):
        self.assertEqual(menu.selected('ALL'),['1','2','3','4','5'])
        self.assertEqual(menu.selected('all u'),['1','2','U','3','4','5'])
        self.assertEqual(menu.selected('5 u 1 U 3'),['1','U','3','5'])
    def test_combined_menu_runs_update_once(self):
        with patch('sys.argv',['menu','--base',self.tmp.name,'--serial','TEST','--steps','ALL U']),patch.object(menu.subprocess,'run',return_value=Mock(returncode=0)) as run,contextlib.redirect_stdout(io.StringIO()):self.assertEqual(menu.main(),0)
        commands=[c.args[0] for c in run.call_args_list]
        self.assertEqual(len(commands),5);self.assertIn('--update',commands[1]);self.assertEqual(sum('--update' in c for c in commands),1)
        self.assertEqual(json.loads((self.s.work/'TEST.setup-plan.json').read_text())['remaining'],[])
    def test_failed_combined_plan_retained(self):
        with patch('sys.argv',['menu','--base',self.tmp.name,'--serial','TEST','--steps','ALL U']),patch.object(menu.subprocess,'run',side_effect=[Mock(returncode=0),Mock(returncode=2)]),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(menu.main(),2)
        self.assertEqual(menu.resume_choice(Path(self.tmp.name),'TEST')[0],['2','U','3','4','5'])
    def test_infer_interrupted_update(self):
        self.tx();self.s.save();self.assertEqual(menu.resume_choice(Path(self.tmp.name),'TEST')[0],['U'])
    def test_one_recovery_session(self):
        self.s.update_flow();a=self.events.index('firmware');b=self.events.index('magisk-flash')
        self.assertEqual(self.events[a:b+1],['firmware','postota','magisk-flash']);self.assertEqual(self.events.count('recovery'),1)
        self.assertIn(PREFIX+'complete',self.s.state['done'])
    def test_reuse_backup(self):
        self.s.state['done']=['unlock','backup'];self.s.update_flow();self.s.backups.assert_not_called();self.s.verify_backups.assert_called()
    def test_uncertain_flash_blocks_writes(self):
        for pending in (PREFIX+'firmware',PREFIX+'postota',PREFIX+'magisk','postota'):
            self.s.state['pending']=pending
            with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.update_firmware_flash.assert_not_called();self.s.flash.assert_not_called()
    def test_resume_after_firmware(self):
        self.tx();self.s.state['done']=['unlock','backup',PREFIX+'firmware'];self.recovery=True
        self.s.update_flow();self.s.update_firmware_flash.assert_not_called();self.s.postota.assert_called_once();self.s.flash.assert_called_once()
    def test_resume_after_magisk(self):
        self.tx();self.s.state['done']=['unlock','backup',PREFIX+'firmware',PREFIX+'postota',PREFIX+'magisk'];self.recovery=True
        self.s.update_flow();self.s.update_firmware_flash.assert_not_called();self.s.postota.assert_not_called();self.s.flash.assert_not_called()
    def test_incomplete_flash_sequence_requires_recovery(self):
        self.tx();self.s.state['done']=['unlock','backup',PREFIX+'firmware']
        with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.postota.assert_not_called()
    def test_bad_backup_blocks_flash(self):
        self.s.verify_backups.side_effect=k.Stop('bad backup')
        with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.update_firmware_flash.assert_not_called()
    def test_bad_postota_blocks_magisk_and_boot(self):
        self.s.postota.side_effect=k.Stop('byte mismatch')
        with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.flash.assert_not_called();self.assertNotIn('boot',self.events)
    def test_completed_update_not_repeated(self):
        self.s.update_flow();self.events.clear();self.s.update_flow();self.assertEqual(self.events,[])
    def test_no_downgrade(self):
        self.s.state['profile']['incremental']='0033018554244'
        with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.confirm.assert_not_called()
    def test_identity_transition_bound_to_target_and_success(self):
        self.tx();self.assertFalse(self.s.update_identity_transition(TARGET));self.s.state['done'].append(PREFIX+'firmware')
        self.assertTrue(self.s.update_identity_transition(TARGET));self.assertFalse(self.s.update_identity_transition(dict(TARGET,fingerprint='other')))
    def identity_mocks(self,kernel):
        self.tx();self.s.state['done']=['unlock','backup',PREFIX+'firmware']
        props={'ro.product.device':'karat','ro.product.model':'AFTMA08C15','ro.build.fingerprint':FINGERPRINT,'ro.build.version.incremental':TARGET['incremental']}
        self.s.prop=Mock(side_effect=lambda key:props.get(key,''));self.s.shell=Mock(return_value=kernel)
    def test_identity_migration(self):
        self.identity_mocks('Linux 5.10.43-android12-9-g76bdd754c12c armv8l');self.s.identity()
        self.assertEqual(self.s.state['profile'],TARGET);self.assertEqual(self.s.update_backup_fingerprint(),SOURCE['fingerprint'])
    def test_wrong_kernel_rejected(self):
        self.identity_mocks('Linux 5.10.43-wrong armv8l')
        with self.assertRaises(k.Stop):self.s.identity()
    def test_preinit_required(self):
        self.s.shell=Mock(return_value='')
        with self.assertRaises(k.Stop):k.Setup.require_preinit(self.s)
        self.s.shell=Mock(return_value='PREINIT_READY');k.Setup.require_preinit(self.s)
    def test_both_vector_types_required(self):
        self.s.shell=Mock(return_value='type xposed_file file_type')
        with self.assertRaises(k.Stop):k.Setup.verify_vector_policy(self.s)
        self.s.shell=Mock(return_value='type xposed_file file_type\ntype xposed_data file_type');k.Setup.verify_vector_policy(self.s)
    def test_preinit_repair_cannot_bypass_prompt(self):
        self.s.require_preinit=Mock(side_effect=[k.Stop('missing'),None]);self.s.a.magisk_ready=True
        self.s.magisk_app=Mock(side_effect=lambda:self.assertFalse(self.s.a.magisk_ready));k.Setup.ensure_preinit(self.s)
        self.s.magisk_app.assert_called_once();self.s.magisk_setup_reboot.assert_called_once();self.assertTrue(self.s.a.magisk_ready)
    def test_verifier_precedes_promotion(self):
        events=[];self.s.verifier=Mock(side_effect=lambda:events.append('verify'));self.s.shell=Mock(side_effect=lambda cmd:events.append(cmd))
        self.s.update_restore_microg();self.assertEqual(events[0],'verify');self.assertIn('rm -f',events[1])
    def test_bad_verifier_blocks_promotion(self):
        self.s.verifier=Mock(side_effect=k.Stop('conflict'));self.s.shell=Mock()
        with self.assertRaises(k.Stop):self.s.update_restore_microg()
        self.s.shell.assert_not_called()
    def active_modules(self):
        self.s.update_modules_off=Mock(side_effect=lambda:self.s.state['firmware_update'].update(restore_modules=['zygisk_vector','microg_installer_revived_again']))
    def test_restore_order(self):
        self.active_modules();self.s.update_restore_vector=Mock(side_effect=lambda:self.events.append('vector'));self.s.update_restore_microg=Mock(side_effect=lambda:self.events.append('microg'));self.s.microg_reboot=Mock(side_effect=lambda:self.events.append('microg-boot'))
        self.s.update_flow();self.assertLess(self.events.index('ensure_preinit'),self.events.index('vector'));self.assertLess(self.events.index('verify_vector_policy'),self.events.index('microg'));self.assertLess(self.events.index('microg'),self.events.index('microg-boot'))
    def test_disabled_modules_preserved(self):
        self.s.update_restore_vector=Mock();self.s.update_restore_microg=Mock();self.s.update_flow();self.s.update_restore_vector.assert_not_called();self.s.update_restore_microg.assert_not_called()
    def test_saved_module_intentions_precede_disable(self):
        self.tx();self.s.state['firmware_update'].pop('restore_modules')
        def shell(cmd,**kwargs):
            if 'echo ENABLED' in cmd:return 'ENABLED'
            if 'touch ' in cmd:self.assertEqual(len(json.loads(self.s.statefile.read_text())['firmware_update']['restore_modules']),2)
            return ''
        self.s.shell=Mock(side_effect=shell);k.Setup.update_modules_off(self.s)
    def test_global_verifier_gate_blocks_reboot(self):
        self.s.shell=Mock(return_value='package:/data/app/play.apk');self.s.verifier=Mock(side_effect=k.Stop('conflict'));self.s.adb=Mock()
        with self.assertRaises(k.Stop):k.Setup.reboot(self.s)
        self.s.adb.assert_not_called()
    def test_firmware_pin(self):
        self.assertEqual(k.FILES[FIRMWARE][1],'559cddbc9e57fa786b396aa4939b54fcb8ff85c789f0ef55df9b0ed4138c7578')
    def flash_setup(self):
        self.s.active_stage=PREFIX+'firmware';self.recovery=True;self.s.file=Mock(return_value='local');self.s.push=Mock()
    def test_pending_after_transfer(self):
        self.flash_setup();self.s.push=Mock(side_effect=lambda *args:self.assertIsNone(self.s.state['pending']))
        def shell(cmd,**kwargs):
            self.assertEqual(self.s.state['pending'],PREFIX+'firmware');return 'ok'
        self.s.shell=Mock(side_effect=shell);k.Setup.flash(self.s,FIRMWARE,'ok')
    def test_transfer_failure_before_pending(self):
        self.flash_setup();self.s.push.side_effect=k.Stop('hash mismatch')
        with self.assertRaises(k.Stop):k.Setup.flash(self.s,FIRMWARE,'ok')
        self.assertIsNone(self.s.state['pending'])
    def test_flash_failure_keeps_pending(self):
        self.flash_setup();self.s.shell=Mock(return_value='error: failed')
        with self.assertRaises(k.Stop):k.Setup.flash(self.s,FIRMWARE,'ok')
        self.assertEqual(self.s.state['pending'],PREFIX+'firmware')
        with self.assertRaises(k.Stop):self.s.update_flow()
    def current_mocks(self):
        self.s.state['profile']=copy.deepcopy(TARGET);self.s.prepare=Mock();self.s.connect=Mock();self.s.resume_ghostlock=Mock();self.s.update_flow=Mock()
    def test_current_firmware_not_flashed(self):
        self.current_mocks();self.s.root_flow();self.s.update_flow.assert_not_called()
    def test_current_firmware_still_runs_selected_phase_two(self):
        self.current_mocks();self.s.a.root_phase='permanent';self.s.a.update=True;self.s.permanent_root=Mock()
        self.s.root_flow();self.s.update_flow.assert_not_called();self.s.permanent_root.assert_called_once()
    def test_bad_vector_policy_blocks_boot_and_microg(self):
        self.active_modules();self.s.update_restore_vector=Mock();self.s.update_restore_microg=Mock();self.s.verify_vector_policy.side_effect=k.Stop('rules missing')
        with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.update_restore_microg.assert_not_called();self.assertNotIn(PREFIX+'vector-boot',self.s.state['done'])
    def firmware_fixture(self,text):
        p=Path(self.tmp.name)/'firmware.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('META-INF/com/android/metadata',text)
        self.s.file=Mock(return_value=p)
    def test_wrong_metadata_blocks_flash(self):
        self.firmware_fixture('pre-device=other\npost-build=other')
        with self.assertRaises(k.Stop):k.Setup.update_firmware_flash(self.s)
        self.s.flash.assert_not_called()
    def test_insufficient_space_blocks_flash(self):
        self.firmware_fixture('pre-device=karat\npost-build='+FINGERPRINT);self.s.shell=Mock(return_value='1')
        with self.assertRaises(k.Stop):k.Setup.update_firmware_flash(self.s)
        self.s.flash.assert_not_called()
    def test_unknown_root_cannot_repeat_unlock(self):
        self.s.shell=Mock(side_effect=lambda cmd,**kw:'uid=0(root)' if cmd=='id' else '')
        self.s.unlock=Mock()
        with self.assertRaises(k.Stop):self.s.update_flow()
        self.s.unlock.assert_not_called();self.s.update_firmware_flash.assert_not_called()
    def test_fresh_unrooted_update_unlocks_once(self):
        self.s.shell=Mock(side_effect=lambda cmd,**kw:('30.7:MAGISK:R' if PREFIX+'magisk' in self.s.state['done'] else '') if cmd=='magisk -v' else 'uid=2000(shell)' if cmd=='id' else '')
        def unlock():self.recovery=True;self.events.append('unlock')
        self.s.unlock=Mock(side_effect=unlock)
        self.s.update_flow();self.s.unlock.assert_called_once();self.s.backups.assert_called_once()
        self.assertEqual(self.events.count('recovery'),0)
        self.assertLess(self.events.index('unlock'),self.events.index('firmware'))
