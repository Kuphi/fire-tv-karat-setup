#!/usr/bin/env python3
"""Cross-platform app installation and compilation. No sdcard cleanup here."""

if __name__ == "__main__":
    import sys
    sys.dont_write_bytecode = True
    from bilingual import run
    sys.exit(run("install_apps_and_optimize", sys.argv[1:]))

import argparse
import hashlib
import json
from pathlib import Path
import sys
if '--dry-run' in sys.argv or '--preview-only' in sys.argv: sys.dont_write_bytecode = True
import urllib.request
import zipfile
import karat as k
import terminal_ui as ui

APPS = [
 ('Netflix', 'com.netflix.ninja', 'com.netflix.ninja*.apk', 'amazon'),
 ('YouTube', 'com.amazon.firetv.youtube', 'com.amazon.firetv.youtube*.apk', 'amazon'),
 ('Prime Video', 'com.amazon.firebat', 'com.amazon.firebat*.apk', 'amazon'),
 ('Disney+', 'com.disney.disneyplus', 'com.disney.disneyplus*.apk', 'amazon'),
 ('Wholphin', 'com.github.damontecres.wholphin', 'com.github.damontecres.wholphin*.apk', 'github'),
 ('CX File Explorer', 'com.cxinventor.file.explorer', '*cx*file*explorer*.apk', 'play'),
]

def parse_app_selection(value):
    value=value.strip()
    if value.upper() in ('ALL','ALLE'):return list(APPS)
    if value.upper() in ('NONE','KEINE'):return []
    numbers=value.replace(',', ' ').split()
    if not numbers or any(not n.isdigit() or not 1<=int(n)<=len(APPS) for n in numbers):
        raise ValueError('Enter numbers 1 to 6, e.g. 1 2 6, or ALL / NONE.')
    return [APPS[i-1] for i in sorted(set(map(int,numbers)))]

def choose_apps(value=None):
    if value is not None:return parse_app_selection(value)
    ui.title('SELECT APPS', 'Only selected apps will be installed and optimized.')
    rows=[]
    for index,(name,_,_,source) in enumerate(APPS,1):
        label='Amazon Appstore' if source=='amazon' else 'GitHub-APK / Play Store' if source=='github' else 'Play Store / matching local APK'
        rows.append((index,name,label))
    ui.menu(rows)
    ui.info('Example: 1 2 6  →  Netflix, YouTube and CX File Explorer')
    ui.info('ALL = all  ·  NONE = no apps  ·  EXIT = exit\n')
    while True:
        try:answer=input('  Your selection → ').strip()
        except EOFError:raise k.Stop('No selection received; run again with --apps "1 2 6".')
        if answer.upper()=='EXIT':return None
        try:return parse_app_selection(answer)
        except ValueError as error:print(error)

class Apps(k.Setup):
    def installed(self, package):
        return self.shell('pm path ' + package, check=False).startswith('package:')

    def local_apk(self, pattern):
        import fnmatch
        files = [p for p in (self.base/'packages').rglob('*') if p.is_file() and fnmatch.fnmatch(p.name.lower(), pattern.lower())]
        if len(files) == 1: return files[0]
        if len(files) > 1: self.log('WARNING: Several matching APKs; use the store: ' + pattern)
        return None

    def install_apk(self, apk, package=None):
        k.archive_ok(apk)
        if package:
            actual, _, _ = k.manifest_metadata(apk)
            k.require(actual == package, 'APK package does not match ' + package)
        self.log('INSTALLATION: '+apk.name)
        output = self.adb('install', '-r', str(apk), timeout=240)
        k.require('Success' in output and 'Failure' not in output, 'Installation failed: '+apk.name)
        self.log('OK: Installed: '+apk.name)

    def wholphin(self):
        request = urllib.request.Request('https://api.github.com/repos/damontecres/Wholphin/releases/latest', headers={'User-Agent':'karat-setup'})
        with urllib.request.urlopen(request, timeout=30) as response: release = json.load(response)
        assets = [a for a in release['assets'] if a['name'].lower().endswith('.apk') and 'debug' not in a['name'].lower()]
        universal = [a for a in assets if 'universal' in a['name'].lower()]
        assets = universal or assets
        k.require(len(assets) == 1, 'No unambiguous matching Wholphin APK; use the store.')
        asset = assets[0]
        url = asset['browser_download_url']
        k.require(url.startswith('https://github.com/damontecres/Wholphin/releases/download/'), 'Unexpected download source')
        target = self.base/'packages/apps/com.github.damontecres.wholphin-official.apk'
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_suffix('.apk.part')
        try:
            self.log('DOWNLOAD: Wholphin from the official GitHub release')
            with urllib.request.urlopen(url, timeout=60) as response, part.open('wb') as output:
                k.require(response.geturl().startswith('https://'), 'Insecure download redirect')
                k.downloads.copy_with_progress(response, output, target.name)
            k.archive_ok(part)
            digest = asset.get('digest')
            if digest and digest.startswith('sha256:'): k.require(k.sha(part)==digest[7:], 'Wholphin SHA256 mismatch')
            part.replace(target)
            return target
        finally:
            if part.exists(): part.unlink()

    def gate(self, message):
        self.log(message, detail=True)
        ui.action(message, [('RESUME','installed / scoped; or intentionally skip'),('EXIT','exit safely')])
        while True:
            try: answer = input('  Your input → ').strip().upper()
            except EOFError: raise k.Stop('No interactive input.')
            if answer == 'RESUME': return
            if answer == 'EXIT': raise k.Stop('Stopped at your request.')
            print('Please type RESUME or EXIT.')

    def run_apps(self, selected=None):
        chosen=list(APPS) if selected is None else selected
        self.connect()
        k.require(self.prop('sys.boot_completed') == '1', 'Android has not fully booted yet.')
        missing, errors = [], []
        self.log('START: Set animation scales to 0.5')
        for key in ('window_animation_scale','transition_animation_scale','animator_duration_scale'):
            self.shell('settings put global '+key+' 0.5')
            k.require(self.shell('settings get global '+key)=='0.5', 'Setting was not applied: '+key)
        for name, package, pattern, source in chosen:
            if self.installed(package):
                self.log('SKIP: '+name+' already installed'); continue
            self.log('START: '+name)
            if source != 'amazon':
                try:
                    apk = self.local_apk(pattern)
                    if not apk and source == 'github': apk = self.wholphin()
                    if apk: self.install_apk(apk, package)
                except (k.Stop, OSError, ValueError, zipfile.BadZipFile) as error:
                    self.log('WARNING: '+str(error))
            if not self.installed(package):
                if source == 'amazon': uri='amzn://apps/android?p='+package
                else: uri='market://details?id='+package
                command = 'am start -a android.intent.action.VIEW -d '+k.shlex.quote(uri)
                if source != 'amazon': command += ' -p com.android.vending'
                output = self.shell(command, check=False)
                if 'Error' in output or 'Exception' in output: self.log('WARNING: Could not open the store page.')
                else: self.gate(name+': install from the store. If unavailable, use RESUME to skip.')
            if not self.installed(package): missing.append(name+' ('+package+')')
        self.log('START: Optimize installed apps')
        for package in ['com.oversea.aslauncher']+[app[1] for app in chosen]:
            if not self.installed(package):
                self.log('SKIP: Optimization skipped, package is missing: '+package)
                if package=='com.oversea.aslauncher': missing.append('Emotn UI ('+package+')')
                continue
            label=next((app[0] for app in APPS if app[1]==package),'Emotn UI')
            self.log('OPTIMIZING: '+label)
            output=self.shell('cmd package compile -m speed -f '+package, timeout=300, check=False)
            if 'Success' not in output: errors.append('Optimization: '+package)
        if self.installed('com.oversea.aslauncher'):
            self.shell('am force-stop com.oversea.aslauncher')
            self.shell('am start -n '+k.HOME)
        if missing: self.log('MISSING APPS:\n  • '+'\n  • '.join(dict.fromkeys(missing)))
        if errors: self.log('WARNING: Failed optimizations:\n  • '+'\n  • '.join(errors))
        self.log('OK: App installation and optimization completed.')

def main():
    parser=argparse.ArgumentParser(description='Install and optimize apps; missing apps are listed at the end.')
    parser.add_argument('--lang', choices=['en','de'], help='Interface language; selected before setup')
    parser.add_argument('--base', default=str(k.HERE.parent))
    parser.add_argument('--serial')
    parser.add_argument('--verbose', action='store_true', help='Show full technical output')
    parser.add_argument('--dry-run', action='store_true', help='Check local APKs/try missing direct downloads; no device required')
    parser.add_argument('--preview-only', action='store_true', help='Output only; no downloads or files')
    parser.add_argument('--apps', help='Selection, e.g. "1 2 6", ALL or NONE')
    args=parser.parse_args()
    if args.dry_run and args.preview_only: parser.error('Do not combine --dry-run and --preview-only')
    selection=args.apps
    if selection is None and (args.dry_run or args.preview_only) and not sys.stdin.isatty(): selection='ALL'
    try: chosen=choose_apps(selection)
    except (ValueError,k.Stop) as error: parser.error(str(error))
    if chosen is None: return 0
    if args.preview_only:
        from dry_run import preview
        return preview('apps', selected_apps=[app[0] for app in chosen])
    engine_args=k.parser().parse_args(['emotn','--base',args.base]+(['--serial',args.serial] if args.serial else []))
    engine_args.verbose=args.verbose
    engine=None
    try:
        engine=Apps(engine_args)
        if args.dry_run:
            missing=[]
            engine.log('DRY RUN: Real downloads/file checks; no ADB connection.')
            for name,package,pattern,source in chosen:
                try:
                    apk=engine.local_apk(pattern)
                    if not apk and source=='github': apk=engine.wholphin()
                    if apk:
                        k.archive_ok(apk)
                        k.require(k.manifest_metadata(apk)[0]==package, 'Wrong APK package: '+name)
                        engine.log('OK: '+name+' checked locally')
                    else: missing.append(name+' (store installation requires a device)')
                except (k.Stop,OSError,ValueError,zipfile.BadZipFile) as error:
                    missing.append(name+': '+str(error))
            if missing:engine.log('MISSING APPS / DOWNLOADS:\n  • '+'\n  • '.join(missing))
            from dry_run import preview
            return preview('apps',downloads=True, selected_apps=[app[0] for app in chosen])
        engine.run_apps(chosen); return 0
    except (k.Stop,OSError,ValueError,zipfile.BadZipFile) as error:
        if engine: engine.log('STOP: '+str(error))
        else: print(str(error),file=sys.stderr)
        return 2
    except KeyboardInterrupt: return 130
    finally:
        if engine: engine.logfile.close(); engine.lock.close()
if __name__=='__main__': sys.exit(main())
