import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import zipfile
import karat as k

class SystemClock(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):self.s=k.Setup(k.parser().parse_args(['emotn','--base',self.tmp.name]))
        self.addCleanup(self.s.lock.close);self.addCleanup(self.s.logfile.close)
        self.s.serial='TEST';self.s.statefile=self.s.work/'TEST.json';self.s.state={'serial':'TEST','done':[],'pending':None};self.s.log=Mock()
    def test_old_clock_removed_only_when_installed(self):
        self.s.shell=Mock(side_effect=['package:/data/app/old/base.apk','Success',''])
        self.s.migrate_clock()
        self.assertEqual(self.s.shell.call_args_list[1].args[0],'pm uninstall local.karat.emotnclock')
    def test_absent_old_clock_is_left_alone(self):
        self.s.shell=Mock(return_value='');self.s.migrate_clock();self.assertEqual(self.s.shell.call_count,1)
    def test_failed_uninstall_blocks_two_clock_modules(self):
        self.s.shell=Mock(side_effect=['package:/old.apk','Failure'])
        with self.assertRaises(k.Stop):self.s.migrate_clock()
    def test_timezone_is_not_forced_and_legacy_scope_is_renewed(self):
        self.s.state['done']=['emotn-snapshot','emotn-home','emotn-settings','emotn-startup','wifi-adb-policy','emotn-scope','emotn-compile','app-EmotnUI','app-Amazon-Appstore-Direct','app-FireTV-Settings-Bridge','app-Emotn-Idle-Timer','app-Emotn-Berlin-Clock']
        self.s.prepare=Mock();self.s.connect=Mock();self.s.root_ok=Mock();self.s.install=Mock();self.s.migrate_clock=Mock();self.s.pause=Mock()
        self.s.prop=Mock(return_value='Asia/Tokyo')
        self.s.shell=Mock(side_effect=lambda cmd,**kw:'30.7:MAGISK:R' if cmd=='magisk -v' else 'OK')
        vector=Path(self.tmp.name)/'vector.zip'
        with zipfile.ZipFile(vector,'w') as z:z.writestr('module.prop','id=zygisk_vector\n')
        self.s.file=Mock(return_value=vector);self.s.emotn_flow()
        self.assertEqual([c.args[0] for c in self.s.install.call_args_list], ['Emotn-System-Clock.apk','Emotn-App-Categories.apk']);self.s.pause.assert_called_once()
        self.assertIn('emotn-categories-scope',self.s.state['done'])
        self.assertIn('emotn-system-clock-scope',self.s.state['done'])
        self.assertFalse(any('timezone' in call.args[0] and ('settings put' in call.args[0] or 'setprop' in call.args[0]) for call in self.s.shell.call_args_list))
    def test_signed_asset_uses_new_identity_and_no_fixed_zone(self):
        p=Path(k.__file__).parent/'assets/Emotn-System-Clock.apk'
        self.assertEqual(k.sha(p),k.FILES[p.name][1])
        self.assertEqual(k.manifest_metadata(p)[:2],('local.karat.emotnsystemclock','1'))
        with zipfile.ZipFile(p) as z:
            dex=z.read('classes.dex');self.assertNotIn(b'Europe/Berlin',dex)
            self.assertIn(b'persist.sys.timezone',dex);self.assertIn(b'android.intent.action.TIMEZONE_CHANGED',dex)
    def test_no_old_clock_is_distributed(self):
        self.assertNotIn('Emotn-Berlin-Clock.apk',k.FILES)
        self.assertFalse((Path(k.__file__).parent/'assets/Emotn-Berlin-Clock.apk').exists())
if __name__=='__main__':unittest.main()
