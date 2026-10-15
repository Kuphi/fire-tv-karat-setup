import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
import karat as k
import install_apps_and_optimize as a

class AppFlow(unittest.TestCase):
    def make_engine(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        args=k.parser().parse_args(['emotn','--base',temp.name])
        with contextlib.redirect_stdout(io.StringIO()):engine=a.Apps(args)
        self.addCleanup(engine.lock.close);self.addCleanup(engine.logfile.close)
        engine.connect=Mock();engine.log=Mock();engine.serial='TEST'
        engine.prop=Mock(return_value='1');engine.gate=Mock();engine.local_apk=Mock(return_value=None)
        engine.file=Mock(side_effect=k.Stop('missing'));engine.wholphin=Mock(side_effect=k.Stop('no download'))
        return engine
    def test_missing_apps_do_not_abort_and_are_reported(self):
        e=self.make_engine();e.installed=Mock(return_value=False)
        e.shell=Mock(side_effect=lambda command,**kwargs:'0.5' if command.startswith('settings get') else 'OK')
        e.run_apps()
        text='\n'.join(c.args[0] for c in e.log.call_args_list)
        self.assertIn('MISSING APPS',text);self.assertIn('Netflix',text)
        self.assertIn('App installation and optimization completed',text)
    def test_existing_apps_compile_after_install_phase(self):
        e=self.make_engine();e.installed=Mock(return_value=True)
        e.shell=Mock(side_effect=lambda command,**kwargs:'0.5' if command.startswith('settings get') else 'Success')
        e.run_apps();e.local_apk.assert_not_called();e.wholphin.assert_not_called()
        commands=[c.args[0] for c in e.shell.call_args_list]
        self.assertIn('cmd package compile -m speed -f com.netflix.ninja',commands)
        self.assertFalse(any('rm ' in c for c in commands))
    def test_amazon_packages_use_amazon_store(self):
        e=self.make_engine();e.installed=Mock(return_value=False)
        e.shell=Mock(side_effect=lambda command,**kwargs:'0.5' if command.startswith('settings get') else 'OK')
        e.run_apps();commands='\n'.join(c.args[0] for c in e.shell.call_args_list)
        for package in ('com.netflix.ninja','com.amazon.firetv.youtube','com.amazon.firebat','com.disney.disneyplus'):
            self.assertIn('amzn://apps/android?p='+package,commands)
            self.assertNotIn('market://details?id='+package,commands)
    def test_wrong_package_apk_rejected_before_install(self):
        e=self.make_engine();e.adb=Mock()
        with patch.object(k,'archive_ok'),patch.object(k,'manifest_metadata',return_value=('wrong.package','1','1')):
            with self.assertRaises(k.Stop):e.install_apk(Path('fake.apk'),'com.netflix.ninja')
        e.adb.assert_not_called()
    def test_wrong_device_never_installs(self):
        e=self.make_engine();e.connect=Mock(side_effect=k.Stop('wrong device'));e.adb=Mock()
        with self.assertRaises(k.Stop):e.run_apps()
        e.adb.assert_not_called()
if __name__=='__main__':unittest.main()

class Selection(unittest.TestCase):
    def test_numbers_select_only_requested_apps(self):
        selected=a.parse_app_selection('1 2 2 6')
        self.assertEqual([app[0] for app in selected],['Netflix','YouTube','CX File Explorer'])
    def test_none_means_no_installation(self):self.assertEqual(a.parse_app_selection('NONE'),[])
    def test_invalid_number_rejected(self):
        with self.assertRaises(ValueError):a.parse_app_selection('8')
    def test_removed_apps_not_available_anywhere(self):
        forbidden={'org.fdroid.fdroid','com.wireguard.android','com.aurora.store','us.materialio.app'}
        self.assertTrue(forbidden.isdisjoint({app[1] for app in a.APPS}))
        for key in k.FILES:self.assertFalse(any(word in key.lower() for word in ('fdroid','wireguard','aurora','materialious')))
    def test_selection_does_not_install_other_apps_or_helper(self):
        engine=AppFlow.make_engine(self);engine.installed=Mock(return_value=True)
        engine.shell=Mock(side_effect=lambda command,**kwargs:'0.5' if command.startswith('settings get') else 'Success')
        engine.run_apps([a.APPS[0]])
        engine.file.assert_not_called();engine.wholphin.assert_not_called()
        commands=[c.args[0] for c in engine.shell.call_args_list]
        self.assertIn('cmd package compile -m speed -f com.netflix.ninja',commands)
        self.assertNotIn('cmd package compile -m speed -f com.amazon.firetv.youtube',commands)
        self.assertNotIn(k.VECTOR,commands)
    def test_main_menu_forwards_app_selection_only_to_phase_five(self):
        import setup_menu as m
        with patch.object(sys,'argv',['setup_menu','--steps','5','--preview-only','--apps','1 6']),patch.object(m.subprocess,'run',return_value=Mock(returncode=0)) as run,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.main(),0)
        command=run.call_args.args[0];self.assertIn('--apps',command);self.assertEqual(command[-1],'1 6')

    def test_categories_belongs_to_emotn_not_app_choices(self):
        self.assertEqual(len(a.APPS),6)
        self.assertNotIn('local.karat.emotncategories',{app[1] for app in a.APPS})
        with self.assertRaises(ValueError):a.parse_app_selection('7')
    def test_emotn_prepare_always_includes_categories(self):
        engine=AppFlow.make_engine(self);engine.a.prepare_only=True;engine.a.categories=False
        engine.prepare=Mock();engine.emotn_flow()
        self.assertIn('Emotn-App-Categories.apk',engine.prepare.call_args.args[0])
