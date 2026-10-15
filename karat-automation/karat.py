#!/usr/bin/env python3
"""Version-bound USB orchestration. No firmware downgrade or recovery rescue."""

if __name__ == "__main__":
    import sys
    sys.dont_write_bytecode = True
    from bilingual import run
    sys.exit(run("karat", sys.argv[1:]))

import argparse
import contextlib
import datetime as dt
import errno
import hashlib
import json
import os
if os.name == 'nt':
    import msvcrt
else:
    import fcntl
import queue
import threading
from pathlib import Path
import re
import selectors
import signal
import shlex
import shutil
import subprocess
import struct
import sys
if '--dry-run' in sys.argv or '--preview-only' in sys.argv: sys.dont_write_bytecode = True
import time
import traceback
import urllib.request
import webbrowser
import downloads
import terminal_ui as ui
import zipfile
from firmware_update import FirmwareUpdate, FIRMWARE, URL as FIRMWARE_URL, SHA256 as FIRMWARE_SHA256, PREFIX as UPDATE_PREFIX

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
MODELS = {'AFTKRT': '4K Max (2nd Gen)', 'AFTKM': '4K (2nd Gen)', 'AFTMA08C15': '4K Plus'}
# Exact author-tested GhostLock profiles supplied by the user. No kernel-only fallback.
SUPPORTED = {
 ('RS8185.3879N', '0033018554244'): ('8.1.8.5', '-g8b4baa819147'),
 ('RS8182.3811N', '0032548774788'): ('8.1.8.2', '-g76bdd754c12c'),
 ('RS8180.3739N', '0032280320768'): ('8.1.8.0', '-g76bdd754c12c'),
 ('RS8180.3729N', '0032280318208'): ('8.1.8.0', '-g76bdd754c12c'),
 ('RS8174.3648N', '0031877644288'): ('8.1.7.4', '-ge1cb3cb5ad98'),
 ('RS8174.3641N', '0031877642496'): ('8.1.7.4', '-ge1cb3cb5ad98'),
 ('RS8169.3556N', '0031139423232'): ('8.1.6.9', '-ge1cb3cb5ad98'),
 ('RS8166.3482N', '0030736751236'): ('8.1.6.6', '-gff609fc8f789'),
 ('RS8160.3380N', '0030501844100'): ('8.1.6.0', '-ga8c852b26125'),
 ('RS8160.3372N', '0030501842052'): ('8.1.6.0', '-ga8c852b26125'),
 ('RS8158.4105N', '0030468475268'): ('8.1.5.8', '-gb7ca23cc70e6'),
 ('RS8155.3474N', '0029998551684'): ('8.1.5.5', '-g05616ee8f7f7'),
 ('RS8153.3202N', '0029528720004'): ('8.1.5.3', '-g05616ee8f7f7'),
 ('RS8149.3133N', '0028723395972'): ('8.1.4.9', '-gb0c9d6e017fb'),
 ('RS8145.3070N', '0028186508932'): ('8.1.4.5', '-gabbd3a8e8dee'),
}
HOME = 'com.oversea.aslauncher/.ui.main.MainActivity'
VECTOR = 'am start -c org.matrix.vector.manager.LAUNCH_MANAGER com.android.shell/.BugreportWarningActivity'
FILES = {
 FIRMWARE: (FIRMWARE_URL, FIRMWARE_SHA256),
 'amonet-karat-v1.3.0.zip': ('https://xdaforums.com/attachments/amonet-karat-v1-3-0-zip.6377986/', '2724ce2515fe37a80112d0c39f36b172a2bb8c23ca742313c17e2866982f5e02'),
 'ghostlock-karat-v1.0.4.zip': ('https://xdaforums.com/attachments/ghostlock-karat-v1-0-4-zip.6386789/', 'b1df5a99c9ca9266be90a02eee62ba717f2cdc8850adf8b7a14fadf091c6532e'),
 'post-ota-karat-v1.0.0.zip': ('https://xdaforums.com/attachments/post-ota-karat-v1-0-0-zip.6379480/', '41ef08753be13b47d08644a7a23767988d8b5a35607e960d5ee6dc8a5cc86159'),
 'Magisk-v30.7.apk': ('https://github.com/topjohnwu/Magisk/releases/download/v30.7/Magisk-v30.7.apk', ''),
 'EmotnUI.apk': ('https://zmautoapp.dangsfly.com/20260711/6a51fff5b0db3.apke8f2.apk', 'ef634633cccb26e8d2beabac37e411f4ca23ce873180d0707274f9e84a7e1610'),
 'google-play/zygisk-next.zip': ('https://github.com/LSPosed/ZygiskNext/releases/download/1.5.0/Zygisk-Next-1.5.0-843-5217106-release.zip', '474d58abc208c0779e7f8f1d8449db755a874d475c13b9cf8decf74bc171933b'),
 'google-play/vector.zip': ('https://github.com/JingMatrix/Vector/releases/download/v2.2/Vector-v2.2-3080-Release.zip', '9ee8323575d615f7b3f1076ff60b2a63a49390ef11881b52632311a37f6f79cc'),
 'google-play/fakegapps.apk': ('https://github.com/whew-inc/FakeGApps/releases/download/6.6/app-release.apk', ''),
 'google-play/microg.apk': ('https://github.com/microg/GmsCore/releases/download/v0.3.15.250932/com.google.android.gms-250932030.apk', ''),
 'google-play/play-store-tv.apk': ('https://www.apkmirror.com/apk/google-inc/google-play-store-android-tv/google-play-store-android-tv-52-0-20-release/google-play-store-android-tv-52-0-20-24-8-pr-937697325-4-android-apk-download/', '16625b025c342c3badb63c60ba4158291863d21fa8bb7e6b16899144ab6037b6'),
 'google-play/microg-installer.zip': ('https://github.com/spacealtctrl/microg_installer_revived_again/releases/download/v1.1.2/microg_installer_revived_again-v1.1.2.zip', ''),
 'Amazon-Appstore-Direct.apk': ('', '1019cbf9644e4dd33fd04874b8058e640c2cdb976a92a83e37d78725a74ada9a'),
 'FireTV-Settings-Bridge.apk': ('', '79820e925dd747cf37f57ee31c3e6f981792f421cc1afb1e5043bafd1afb4878'),
 'Emotn-System-Clock.apk': ('', '7d8277c267f104e0b5754c176f4379ab99dd861876fd94a77b1089b4da62b793'),
 'Emotn-Idle-Timer.apk': ('', '81966add6f9ffbd4515507471b75f0098cdf965974bc4276253f154a5115cba6'),
 'Emotn-App-Categories.apk': ('', 'bb8be35be40ea9d7a29bd67b846ff8ad897a5f48fdb0a11917fc18840e914f9d'),
}

def payload_path(name):
    if name == FIRMWARE: return Path('packages/root') / FIRMWARE
    filename = Path(name).name
    if name.startswith('google-play/'): return Path('packages/google-play') / filename
    if filename in ('amonet-karat-v1.3.0.zip','ghostlock-karat-v1.0.4.zip','post-ota-karat-v1.0.0.zip','Magisk-v30.7.apk','Magisk-v30.7.zip'):
        return Path('packages/root') / filename
    if filename in ('Amazon-Appstore-Direct.apk','FireTV-Settings-Bridge.apk','Emotn-System-Clock.apk','Emotn-Idle-Timer.apk','Emotn-App-Categories.apk'):
        return Path('packages/emotn/helpers') / filename
    if filename == 'EmotnUI.apk': return Path('packages/emotn') / filename
    return Path('packages/apps') / filename


class Stop(RuntimeError): pass

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def require(ok, message):
    if not ok: raise Stop(message)

def archive_ok(path):
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None, f'Damaged archive: {path}')
        for i in z.infolist():
            p = Path(i.filename)
            require(not p.is_absolute() and '..' not in p.parts, 'Unsafe ZIP path')
            require((i.external_attr >> 16) & 0o170000 != 0o120000, 'ZIP contains a symlink')

def atomic_json(path, value):
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        f.flush(); os.fsync(f.fileno())
    tmp.replace(path)
    if os.name != 'nt':
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)

def manifest_metadata(path):
    """Read literal identity from AOSP binary XML; never guess resource values."""
    try:
        with zipfile.ZipFile(path) as z:
            info = z.getinfo('AndroidManifest.xml')
            require(info.file_size <= 4*1024*1024, 'APK manifest is too large.')
            data = z.read(info)
        def read(fmt, offset, end):
            require(0 <= offset <= end-struct.calcsize(fmt), 'APK manifest is truncated.')
            return struct.unpack_from(fmt, data, offset)
        kind, hs, total = read('<HHI', 0, len(data))
        require(kind == 3 and 8 <= hs <= total == len(data), 'Invalid binary APK manifest.')
        pos, strings = hs, None
        while pos < total:
            kind, hs, size = read('<HHI', pos, total)
            end = pos+size
            require(8 <= hs <= size and end <= total, 'Invalid APK manifest block.')
            if kind == 1:
                require(strings is None and hs >= 28, 'Invalid APK string pool.')
                count, styles, flags, start, style_start = read('<IIIII', pos+8, end)
                require(hs+4*(count+styles) <= start <= size, 'Invalid APK string offsets.')
                string_end = pos+(style_start or size)
                require(pos+start <= string_end <= end, 'Invalid APK string boundary.')
                strings = []
                def length(offset, wide):
                    unit, mask = (2, 0x8000) if wide else (1, 0x80)
                    fmt = '<H' if wide else '<B'
                    value = read(fmt, offset, string_end)[0]; offset += unit
                    if value & mask:
                        value = ((value & (mask-1)) << (16 if wide else 8)) | read(fmt, offset, string_end)[0]
                        offset += unit
                    return value, offset
                for i in range(count):
                    offset = pos+start+read('<I', pos+hs+4*i, end)[0]
                    require(offset >= pos+start, 'Invalid APK string offset.')
                    if flags & 0x100:
                        _, offset = length(offset, False)
                        n, offset = length(offset, False)
                        require(offset+n < string_end and data[offset+n] == 0, 'Invalid APK string.')
                        strings.append(data[offset:offset+n].decode('utf-8'))
                    else:
                        n, offset = length(offset, True)
                        require(offset+2*n+2 <= string_end and data[offset+2*n:offset+2*n+2] == b'\0\0', 'Invalid APK string.')
                        strings.append(data[offset:offset+2*n].decode('utf-16-le'))
            elif kind == 0x102:
                require(strings is not None and hs >= 16, 'APK string pool is missing.')
                def string(index):
                    require(index < len(strings), 'Invalid APK string index.')
                    return strings[index]
                ext = pos+hs
                _, tag, attr_start, attr_size, count = read('<IIHHH', ext, end)
                require(string(tag) == 'manifest', 'APK root element is not manifest.')
                require(attr_start >= 20 and attr_size >= 20 and ext+attr_start+count*attr_size <= end, 'Invalid APK attributes.')
                values = {}
                for i in range(count):
                    ns, key, raw, vs, reserved, vt, value = read('<IIIHBBI', ext+attr_start+i*attr_size, end)
                    key = string(key)
                    wanted = (key == 'package' and ns == 0xffffffff) or (key in ('versionName', 'versionCode') and ns != 0xffffffff and string(ns) == 'http://schemas.android.com/apk/res/android')
                    if not wanted: continue
                    require(key not in values and vs == 8 and reserved == 0, 'Ambiguous APK metadata.')
                    if vt == 3: values[key] = string(value)
                    elif key == 'versionCode' and vt in (0x10, 0x11): values[key] = str(value)
                    else: raise Stop('APK metadata uses resource references; --aapt is required.')
                require(all(values.get(k) for k in ('package', 'versionCode', 'versionName')), 'APK package or version is missing.')
                return values['package'], values['versionCode'], values['versionName']
            pos = end
        raise Stop('APK manifest contains no root element.')
    except (KeyError, UnicodeError, struct.error, zipfile.BadZipFile) as e:
        raise Stop(f'Cannot read APK metadata: {e}') from e

class Setup(FirmwareUpdate):
    def __init__(self, args):
        self.a = args
        self.base = Path(args.base).expanduser().resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        legacy_work = self.base / '.karat-setup'
        new_work = self.base / 'karat-automation/runtime'
        require(not (legacy_work.exists() and new_work.exists()), 'Two checkpoint folders exist; automatic merging is disabled.')
        self.work = legacy_work if legacy_work.exists() else new_work
        self.work.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock = open(self.work / 'lock', 'a+b')
        try:
            if os.name == 'nt':
                if self.lock.seek(0, 2) == 0: self.lock.write(b'0'); self.lock.flush()
                self.lock.seek(0)
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            raise Stop('A setup is already running in this directory.')
        stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.logfile = open(self.work / f'{stamp}-{args.flow}.log', 'a', buffering=1, encoding='utf-8')
        os.chmod(self.logfile.name, 0o600)
        self.serial = None
        self.state = {}
        self.statefile = None
        self.active_stage = None
        sourcefile = self.base / 'config/sources.local.json'
        if not sourcefile.exists(): sourcefile = self.base / 'sources.local.json'
        self.sources = json.loads(sourcefile.read_text(encoding='utf-8')) if sourcefile.exists() else {}
        self.log(f'LOG: {self.logfile.name}; Mode={args.flow}; Files={self.base}')
        self.log(f'HOST: Python={sys.version.split()[0]}; Script-SHA256={sha(Path(__file__))}')

    def log(self, s, detail=False):
        if getattr(self, 'live_progress', None): self.live_progress.clear()
        line = f'[{dt.datetime.now().astimezone().isoformat(timespec="seconds")}] {s}'
        self.logfile.write(line + '\n')
        if getattr(self.a, 'verbose', False): print(line, flush=True)
        else: ui.event(s, detail=detail)

    def run(self, argv, timeout=60, check=True):
        self.log('$ ' + shlex.join(str(a) for a in argv), detail=True)
        started = time.monotonic()
        protected = (len(argv) >= 5 and argv[0] == 'adb' and argv[3] == 'shell' and
                     (str(argv[4]).startswith('twrp install ') or
                      str(argv[4]).startswith('magisk --install-module ') or
                      argv[4] == 'su -c /data/local/tmp/unlock'))
        handlers = {}
        transfer = len(argv) >= 4 and argv[0] == 'adb' and argv[3] in ('pull', 'push')
        master = slave = None
        installing = len(argv) >= 4 and argv[0] == 'adb' and argv[3] == 'install'
        self.live_progress = None
        if protected:
            self.log('WRITE IN PROGRESS: No automatic timeout cancellation. Keep USB and power connected.')
            for sig in (signal.SIGINT, signal.SIGTERM):
                handlers[sig] = signal.signal(sig, lambda *_: self.log('Cancellation deferred during writing; wait for completion.'))
        try:
            if transfer and os.name != 'nt':
                master, slave = os.openpty()
                self.log('TRANSFER: Native ADB progress display enabled.')
            p = subprocess.Popen([str(a) for a in argv], stdout=slave if slave is not None else subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=protected and os.name != 'nt')
            if installing:
                self.live_progress = ui.Progress('Installing APK · waiting for Android')
            if slave is not None:
                os.close(slave); slave = None
                stream = os.fdopen(master, 'rb', buffering=0); master = None
            else:
                stream = p.stdout
            chunks = []
            deadline = time.monotonic() + timeout
            progress = time.monotonic() + 30
            output_queue = queue.Queue()
            def reader():
                try:
                    while True:
                        try: raw = os.read(stream.fileno(), 65536)
                        except OSError as error:
                            if transfer and error.errno == errno.EIO: break
                            output_queue.put(error); break
                        if not raw: break
                        output_queue.put(raw)
                finally: output_queue.put(None)
            thread = threading.Thread(target=reader, daemon=True)
            thread.start()
            with stream:
                while True:
                    if self.live_progress: self.live_progress.update()
                    if time.monotonic() >= deadline:
                        if protected:
                            self.log(f'WRITE IN PROGRESS for more than {timeout}s; keep USB and power connected.')
                            deadline = time.monotonic() + timeout
                        else:
                            p.kill(); p.wait()
                            raise Stop(f'Timeout after {timeout}s. No automatic retry.')
                    try: item = output_queue.get(timeout=0.2)
                    except queue.Empty: item = b''
                    if item is None: break
                    if isinstance(item, Exception): raise item
                    if item:
                        chunks.append(item)
                        rendered = item.decode(errors='replace')
                        if transfer:
                            rendered = re.sub(r'\x1b\[[0-9;?]*[ -/]*[@-~]', '', rendered).replace('\r\n', '\n').replace('\r', '\n')
                        if rendered.strip():
                            self.log(rendered.strip(), detail=True)
                            if transfer and not getattr(self.a, 'verbose', False): ui.transfer(rendered.strip())
                    if time.monotonic() >= progress:
                        self.log('Command is still running; keep USB and power connected.')
                        progress = time.monotonic() + 30
            thread.join(timeout=1)
            try: p.wait(timeout=None if protected else max(1, deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                p.kill(); p.wait()
                raise Stop(f'Timeout after {timeout}s. No automatic retry.')
            raw = b''.join(chunks)
        except FileNotFoundError: raise Stop(f'Missing tool: {argv[0]}')
        except KeyboardInterrupt:
            if 'p' in locals() and p.poll() is None:
                p.terminate(); p.wait()
            raise
        finally:
            if self.live_progress:
                self.live_progress.close()
                self.live_progress = None
            for fd in (master, slave):
                if fd is not None: os.close(fd)
            for sig, handler in handlers.items(): signal.signal(sig, handler)
            self.log(f'COMMAND FINISHED: Duration={time.monotonic()-started:.1f}s')
        out = raw.decode(errors='replace').replace('\r', '')
        self.log(f'EXIT: {p.returncode}')
        if check: require(p.returncode == 0, f'Command failed (exit {p.returncode}).')
        return out.strip()

    def adb(self, *args, timeout=60, check=True):
        return self.run(['adb', '-s', self.serial, *args], timeout, check)

    def shell(self, cmd, timeout=60, check=True):
        return self.adb('shell', cmd, timeout=timeout, check=check)

    def prop(self, key): return self.shell('getprop ' + key)

    def connect(self):
        require(shutil.which('adb'), 'adb is missing; install Android Platform Tools.')
        lines = self.run(['adb', 'devices', '-l']).splitlines()
        devices = [s for s in lines if re.match(r'^\S+\s+(device|recovery)\s', s) and 'usb:' in s]
        if os.name == 'nt' and not devices:
            # Some Windows ADB builds omit usb: from the long device listing.
            usb_serial = self.run(['adb', '-d', 'get-serialno'], check=False).strip()
            devices = [s for s in lines if re.match(r'^\S+\s+(device|recovery)\s', s) and s.split()[0] == usb_serial]
        if self.a.serial:
            devices = [s for s in devices if s.split()[0] == self.a.serial]
        require(len(devices) == 1, 'Exactly one authorized USB device is required (use --serial for multiple devices).')
        self.serial = devices[0].split()[0]
        require(re.fullmatch(r'[A-Za-z0-9_-]+', self.serial), 'Unerwartete USB-Seriennummer.')
        self.statefile = self.work / f'{self.serial}.json'
        if self.statefile.exists(): self.state = json.loads(self.statefile.read_text(encoding='utf-8'))
        else: self.state = {'serial': self.serial, 'done': [], 'pending': None}
        require(self.state.get('serial') == self.serial and isinstance(self.state.get('done'), list), 'Checkpoint does not match the USB serial number.')
        self.backup = self.base / 'backups' / self.serial / 'automation-before-root'
        self.identity()

    def identity(self):
        require(self.prop('ro.product.device') == 'karat', 'STOP: Device is not karat.')
        if self.prop('ro.twrp.version'):
            require(self.prop('ro.twrp.version') == '3.7.1_12-0', 'Different TWRP version.')
            require('unlock' in self.state['done'] or self.state.get('pending') == 'unlock' or getattr(self, 'verifying_existing', False),
                    'Unknown recovery state; boot Fire OS once and check the device identity.')
            profile = self.state.get('profile', {})
            key = (profile.get('build'), profile.get('incremental'))
            require(key in SUPPORTED and profile.get('kernel_suffix') == SUPPORTED[key][1],
                    'No previously verified supported firmware in the checkpoint. Check device identity in Fire OS.')
        else:
            require(self.prop('ro.product.model') in MODELS, 'Wrong model: only 4K/4K Max 2nd Gen and 4K Plus are supported.')
            fingerprint = self.prop('ro.build.fingerprint')
            match = re.fullmatch(r'Amazon/karat/karat:11/([^/]+)/([0-9]+):user/amz-p,release-keys', fingerprint)
            require(match, 'Unexpected firmware fingerprint.')
            key = (match.group(1), match.group(2))
            require(key in SUPPORTED, 'Build/incremental is not in the supported list; no exploit or flash will run.')
            require(self.prop('ro.build.version.incremental') == key[1], 'Incremental version and fingerprint do not match.')
            kernel = self.shell('uname -a')
            release = re.search(r'\b5\.10\.\S+', kernel)
            expected_suffix = SUPPORTED[key][1]
            require(release and release.group(0).endswith(expected_suffix) and re.search(r'\barmv8l\b', kernel),
                    'Kernel does not match the build/incremental combination.')
            profile = {'build':key[0], 'incremental':key[1], 'fire_os':SUPPORTED[key][0],
                       'kernel_suffix':expected_suffix, 'fingerprint':fingerprint}
            require(self.state.get('profile') or (not self.state['done'] and not self.state.get('pending')),
                    'Old checkpoint has no firmware profile: do not automatically adopt it for a supported build.')
            require(not self.state.get('profile') or self.state['profile'] == profile or self.update_identity_transition(profile),
                    'Firmware changed since the checkpoint; completed stages cannot be transferred to different firmware.')
            self.state['profile'] = profile
            self.save()

    def save(self): atomic_json(self.statefile, self.state)
    def finish(self, name):
        if name not in self.state['done']: self.state['done'].append(name)
        self.state['pending'] = None
        self.save()

    def stage(self, name, fn, risky=False):
        if name in self.state['done']:
            self.log(f'SKIP: {name} (already completed)'); return
        pending = self.state.get('pending')
        require(not pending, f'Uncertain write operation {pending}: do not repeat it. Check the log; remain in recovery.')
        self.log(f'START: {name}')
        self.active_stage = name
        if risky:
            self.state['pending'] = name; self.save()
        fn()
        self.finish(name)
        self.log(f'OK: {name}')
        self.active_stage = None

    def file(self, name):
        path = self.base / payload_path(name)
        legacy = self.base / name
        if not path.exists() and legacy.exists(): path = legacy
        url, expected = FILES[name]
        custom = self.sources.get(name, {})
        url = custom.get('url') or url
        if custom.get('sha256'):
            require(not expected or custom['sha256'] == expected, f'Pinned hash must not be changed: {name}')
            expected = custom['sha256']
        if not path.exists():
            included = HERE / 'assets' / Path(name).name
            if included.exists():
                path.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(included, path)
                self.log(f'BUNDLE → {name}')
            else:
                require(url.startswith('https://'), f'{name} is missing: add an approved direct HTTPS link to sources.local.json; see README.')
                path.parent.mkdir(parents=True, exist_ok=True)
                part = path.with_name(path.name + '.part')
                self.log(f'DOWNLOAD (file missing): {name}')
                try:
                    with downloads.open_download(url, timeout=60) as r, open(part, 'wb') as f:
                        require(r.geturl().startswith('https://'), 'Download redirected to HTTP.')
                        downloads.copy_with_progress(r, f, Path(name).name)
                    require(part.stat().st_size > 0, 'Empty download.')
                    try: archive_ok(part)
                    except zipfile.BadZipFile:
                        raise Stop(f'{name}: Download is not an APK/ZIP (possibly an HTML page or expired download link). Place the file manually at {path}.')
                    if expected: require(sha(part) == expected, f'Hash mismatch: {name}')
                    part.replace(path)
                finally:
                    if part.exists(): part.unlink()
        require(path.is_file() and path.stat().st_size > 0, f'Empty/invalid file: {name}')
        archive_ok(path)
        if path.suffix == '.apk': self.apk_metadata(name, path)
        if name in ('google-play/zygisk-next.zip','google-play/vector.zip','google-play/microg-installer.zip'):
            with zipfile.ZipFile(path) as z:
                prop = z.read('module.prop').decode()
                target = {'google-play/zygisk-next.zip': '843', 'google-play/vector.zip': '3080'}.get(name)
                if target: require(re.search(r'^versionCode='+target+r'\s*$', prop, re.M), f'Wrong module build: {name}')
                else: require(re.search(r'^version=v?1\.1\.2\s*$', prop, re.M), 'Wrong microG installer.')
        digest = sha(path)
        require(not expected or digest == expected, f'SHA-256 mismatch: {name}; file was not replaced!')
        self.log(f'FILE: {name}; SHA256={digest}; already available; not downloading again')
        # A hash without a known reference value records the file state; it does not prove authenticity.
        inventory = self.work / 'file-hashes.json'
        hashes = json.loads(inventory.read_text(encoding='utf-8')) if inventory.exists() else {}
        require(name not in hashes or hashes[name] == digest, f'File changed since the previous run: {name}')
        hashes[name] = digest; atomic_json(inventory, hashes)
        return path

    def apk_metadata(self, name, path):
        tool = self.a.aapt or shutil.which('aapt') or shutil.which('aapt2')
        if tool:
            out = self.run([tool, 'dump', 'badging', str(path)])
            m = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", out)
            require(m, 'Cannot read APK metadata.')
            actual_package, actual_code, actual_version = m.groups()
        else:
            actual_package, actual_code, actual_version = manifest_metadata(path)
            self.log(f'APK: internal manifest check; Package={actual_package}; Version={actual_version}; Code={actual_code}')
        targets = {
          'Magisk-v30.7.apk': ('com.topjohnwu.magisk','30.7'),
          'EmotnUI.apk': ('com.oversea.aslauncher','1.1.0.2'),
          'google-play/fakegapps.apk': ('inc.whew.android.fakegapps','6.6'),
          'google-play/microg.apk': ('com.google.android.gms','0.3.15.250932'),
          'google-play/play-store-tv.apk': ('com.android.vending','52.0.20-24'),
        }
        if name in targets:
            package, version = targets[name]
            correct_version = version is None or actual_version == version or (name == 'google-play/play-store-tv.apk' and actual_version.startswith(version+' '))
            require(actual_package == package and correct_version, f'Wrong APK/package/version: {name}')

    def import_browser_download(self, name):
        target = self.base / payload_path(name)
        expected = FILES[name][1] or self.sources.get(name, {}).get('sha256')
        if not expected: return False
        requested = Path(name).name
        stem, suffix = Path(requested).stem, Path(requested).suffix
        pattern = re.compile(re.escape(stem) + r'(?: \(\d+\))?' + re.escape(suffix), re.I)
        downloads = Path.home() / 'Downloads'
        if not downloads.is_dir(): return False
        candidates = [p for p in downloads.iterdir() if p.is_file() and pattern.fullmatch(p.name)]
        for candidate in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                if sha(candidate) != expected: continue
                archive_ok(candidate)
                target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.with_name(target.name + '.browser-part')
                try:
                    shutil.copy2(candidate, temp)
                    require(sha(temp) == expected, 'Browser download changed while copying.')
                    temp.replace(target)
                finally:
                    if temp.exists(): temp.unlink()
                self.log(f'OK: Browser download verified using SHA256 and imported: {target}')
                return True
            except (OSError, Stop, zipfile.BadZipFile): continue
        return False

    def manual_download(self, name, error):
        path = self.base / payload_path(name)
        url = self.sources.get(name, {}).get('url') or FILES[name][0]
        if name == 'google-play/play-store-tv.apk':
            url = 'https://www.apkmirror.com/apk/google-inc/google-play-store-android-tv/google-play-store-android-tv-52-0-20-release/google-play-store-android-tv-52-0-20-24-8-pr-937697325-4-android-apk-download/'
        elif name == 'google-play/zygisk-next.zip':
            url = 'https://github.com/LSPosed/ZygiskNext/releases'
        if not url: url = 'See SOURCES.md / config/required-files.json for the appropriate source.'
        headers = getattr(error, 'headers', {}) or {}
        if headers.get('cdn-challenge', '').lower() == 'true':
            self.log('WARNING: The download site requires browser confirmation; direct HTTP downloads are blocked.')
        if url.startswith('https://') and sys.stdin.isatty():
            try:
                if webbrowser.open(url, new=2): self.log('Browser opened. Start the download there or complete the browser confirmation.')
            except Exception: pass
        while True:
            print('\n════════════════════════════════════════════════════════════', flush=True)
            print('  PLEASE DOWNLOAD THE FILE IN YOUR BROWSER', flush=True)
            print('════════════════════════════════════════════════════════════', flush=True)
            self.log(f'Automatic download / file check failed: {error}')
            print(f'\n  1. Open this link:\n     {url}', flush=True)
            print(f'\n  2. Download the matching file: {Path(name).name}', flush=True)
            versions = {'google-play/zygisk-next.zip':'Zygisk Next 1.5.0, Build 843', 'google-play/play-store-tv.apk':'Google Play Store Android TV 52.0.20-24 [8] [PR] 937697325'}
            if name in versions: print('     Required version: '+versions[name], flush=True)
            print(f'\n  3. Move it to this folder:\n     {path.parent}', flush=True)
            print(f'\n  4. The file must have exactly this name:\n     {path.name}', flush=True)
            print('\n  Alternatively, save it in your usual Downloads folder:', flush=True)
            print(f'     {Path.home() / "Downloads"}', flush=True)
            print('  After RESUME, the matching file is automatically verified using SHA256 and copied.', flush=True)
            print('  Do NOT extract ZIP files. Use an APK, not APKM/XAPK.', flush=True)
            print('  Then type RESUME. The script checks the file and continues.', flush=True)
            print('  EXIT explicitly ends the process. Pressing Enter alone does not confirm anything.\n', flush=True)
            try: answer = input('RESUME / EXIT: ').strip().upper()
            except EOFError: raise Stop(f'No interactive input. Place the file at {path} and run the same command again.')
            if answer == 'EXIT': raise Stop('Download stopped at your request; existing files/checkpoints are preserved.')
            if answer != 'RESUME':
                print('Please type RESUME or EXIT.', flush=True)
                continue
            legacy = self.base / name
            self.import_browser_download(name)
            if not path.is_file() and not legacy.is_file():
                error = f'File not found yet: {path}'
                continue
            try:
                result = self.file(name)
            except (Stop, OSError, ValueError, zipfile.BadZipFile) as e:
                error = str(e)
                continue
            self.log(f'OK: Manually supplied file verified: {name}')
            return result

    def prepare(self, names):
        ui.section(f'Prepare files · {len(names)} required')
        for index, name in enumerate(names, 1):
            self.log(f'FILE CHECK: [{index}/{len(names)}] {name}')
            try: self.file(name)
            except (Stop, OSError, ValueError, zipfile.BadZipFile) as error:
                self.manual_download(name, error)

    def push(self, local, remote):
        self.adb('push', str(local), remote, timeout=300)
        remote_hash = self.shell('sha256sum ' + shlex.quote(remote)).split()[0]
        require(remote_hash == sha(local), 'Transfer hash mismatch; no flash will run.')

    def wait(self, recovery=False, seconds=360, previous_boot=None):
        self.log('Waiting for TWRP' if recovery else 'Waiting for Android boot_completed=1')
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            try:
                value = self.prop('ro.twrp.version') if recovery else self.prop('sys.boot_completed')
                ready = value == ('3.7.1_12-0' if recovery else '1') and (recovery or not self.prop('ro.twrp.version'))
                if ready and previous_boot:
                    current = self.shell('cat /proc/sys/kernel/random/boot_id')
                    ready = bool(current) and current != previous_boot
            except Stop: pass
            else:
                if ready:
                    self.identity(); return
            time.sleep(3)
        raise Stop('Boot timeout. Do not reboot automatically; keep USB connected and check the log.')

    def reboot(self, recovery=False):
        if not self.prop('ro.twrp.version') and self.prop('sys.boot_completed') == '1':
            if self.shell('pm path com.android.vending', check=False).startswith('package:'):
                self.verifier()
        previous = self.shell('cat /proc/sys/kernel/random/boot_id')
        require(re.fullmatch(r'[0-9a-f-]{36}', previous), 'Cannot read boot ID; no automatic reboot.')
        self.adb('reboot', *(['recovery'] if recovery else []))
        # Avoid accepting stale properties from the previous running transport.
        time.sleep(5)
        self.wait(recovery, previous_boot=previous)

    def root_ok(self): require('uid=0(' in self.shell('id'), 'Root ADB is unavailable.')

    def recovery_ready(self, seconds=180):
        """Probe the ORS command service, not only early ro.twrp.version."""
        self.log('Waiting for the TWRP command service and internal storage to become ready.')
        deadline = time.monotonic() + seconds
        token = 'KARAT_READY_' + str(time.monotonic_ns())
        while time.monotonic() < deadline:
            try:
                require(self.prop('ro.twrp.version') == '3.7.1_12-0', 'TWRP is not reachable yet.')
                out = self.shell('twrp print ' + token, timeout=15)
                if token in out and 'Done processing script file' in out:
                    mounted = self.shell("test -d /data/media/0 && test -d /sdcard && grep -q ' /data ' /proc/mounts && echo STORAGE_READY")
                    if mounted == 'STORAGE_READY':
                        self.log('TWRP READY: ORS response complete; /data and /sdcard are accessible.')
                        return
            except Stop as e:
                # A hung probe may still be pending on the device: do not queue more.
                if 'Timeout' in str(e):
                    raise Stop('TWRP command service did not respond in time or is busy. No backup/flash started; let the current TWRP operation finish.') from e
            time.sleep(3)
        raise Stop('TWRP did not become ready. No backup/flash started; check the recovery log.')

    def recovery_backup(self, spec, label, words):
        remote = f'/sdcard/TWRP/BACKUPS/{self.serial}/{label}'
        present = self.shell(f'if [ -e {remote} ]; then echo PRESENT; else echo ABSENT; fi')
        require(present in ('PRESENT', 'ABSENT'), 'Backup destination state is uncertain.')
        if present == 'PRESENT':
            out = self.shell('cat ' + remote + '/recovery.log')
            marker = out.rfind(' * Backup Folder:')
            require(marker >= 0, 'Existing backup has no matching completion log; it was not overwritten.')
            out = out[marker:]
            require(label in out.splitlines()[0] and '[BACKUP COMPLETED IN ' in out and
                    all('Backing up ' + w in out for w in words),
                    'Existing backup is incomplete or its completion is uncertain; it was not overwritten.')
            self.log(f'ADOPT BACKUP: {label}; completion confirmed in the matching recovery.log.')
        else:
            out = self.shell(f'twrp backup {spec} {label}', timeout=1800)
            require('Backup Complete' in out and all('Backing up ' + w in out for w in words), 'TWRP backup is incomplete.')
        # Validate every backup archive against the digest TWRP generated.
        listing = self.shell(f'ls -1 {remote}')
        archives = [n for n in listing.splitlines() if re.fullmatch(r'(boot|data|system)\.[A-Za-z0-9_.-]+\.win[0-9]*', n)]
        for word in words:
            require(any(n.startswith(word.lower()+'.') for n in archives), f'{word} backup is missing.')
        for name in archives:
            require(name+'.sha2' in listing.splitlines(), f'Backup checksum is missing: {name}')
            result = self.shell(f'cd {remote} && sha256sum -c {name}.sha2', timeout=300)
            require('OK' in result and 'FAILED' not in result, f'Backup checksum mismatch: {name}')

    def install(self, name):
        self.log('INSTALLATION: '+Path(name).name)
        out = self.adb('install', '-r', str(self.file(name)), timeout=240)
        require('Success' in out and 'Failure' not in out, 'APK installation failed.')
        self.log('OK: Installed: '+Path(name).name)

    def verify_magisk_app(self, apk):
        require(apk.stat().st_size > 5 * 1024 * 1024, 'Local Magisk APK is too small: the full v30.7 APK is required, not a stub.')
        paths = self.shell('pm path com.topjohnwu.magisk').splitlines()
        require(len(paths) == 1 and paths[0].startswith('package:/'), 'Magisk app path is ambiguous.')
        installed = paths[0][len('package:'):].strip()
        digest = self.shell('sha256sum ' + shlex.quote(installed)).split()
        require(digest and digest[0] == sha(apk), 'Installed Magisk app does not match the full local v30.7 APK.')
        self.log('Magisk app: full local APK verified on the device using SHA256.')

    def ensure_magisk_app(self, apk):
        for attempt in (1, 2):
            self.log(f'Magisk app: local installation {attempt}/2')
            self.shell('am force-stop com.topjohnwu.magisk')
            try:
                self.install('Magisk-v30.7.apk')
                self.verify_magisk_app(apk)
                return
            except Stop as error:
                self.log(f'Full Magisk app has not been verified yet: {error}')
        self.log('Local repair failed. Wi-Fi is being enabled for manual installation.')
        self.shell('svc wifi enable')
        self.pause('magisk_ready', 'Connect to Wi-Fi and install/download the full Magisk app v30.7. Use the local Magisk-v30.7.apk if needed. Then RESUME; EXIT ends the process.', 'am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.topjohnwu.magisk')
        self.verify_magisk_app(apk)

    def magisk_app(self):
        apk = self.file('Magisk-v30.7.apk')
        require(apk.stat().st_size > 5 * 1024 * 1024, 'Local Magisk APK is a stub or incomplete.')
        self.ensure_magisk_app(apk)
        out = self.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.topjohnwu.magisk')
        components = [line.strip() for line in out.splitlines() if re.fullmatch(r'com\.topjohnwu\.magisk/[A-Za-z0-9_.$]+', line.strip())]
        require(len(components) == 1, 'The full Magisk app has no unambiguous launcher activity.')
        self.pause('magisk_ready', 'Full Magisk app installed locally. Select Install → Direct Install (Recommended), then wait until it finishes. Then type RESUME here: the script will reboot the Stick and wait for Android. You do not need to press Reboot in Magisk. An app download is normally unnecessary.', 'am start -n ' + shlex.quote(components[0]))
        try:
            self.verify_magisk_app(apk)
        except Stop:
            self.ensure_magisk_app(apk)

    def flash(self, name, marker):
        require(self.prop('ro.twrp.version') == '3.7.1_12-0', 'Flashing is allowed only in verified TWRP.')
        self.recovery_ready()
        remote = '/sdcard/' + ('Magisk-v30.7.zip' if name == 'Magisk-v30.7.apk' else Path(name).name)
        self.push(self.file(name), remote)
        if self.active_stage == 'postota' or ((self.active_stage or '').startswith(UPDATE_PREFIX) and self.active_stage.endswith(('firmware', 'postota', 'magisk'))):
            # Mark the write only after all read-only checks and transfer validation.
            self.state['pending'] = self.active_stage
            self.save()
            self.log('POSTOTA: Preflight passed; starting the flash now.' if self.active_stage == 'postota' else 'UPDATE: Checks and transfer verified; starting the flash now.')
        out = self.shell('twrp install ' + shlex.quote(remote), timeout=600)
        require(marker in out and not re.search(r'(^|\n).*\b(abort|failed|error)\b', out, re.I),
                'Installer meldet keinen eindeutigen Erfolg. In TWRP bleiben!')

    def confirm(self, token, text):
        ui.action(text, [(token, 'explicitly start this step'), ('EXIT', 'exit safely')])
        while True:
            try: answer = input('  Your input → ').strip().upper()
            except EOFError: raise Stop('No confirmation received; the step was not started.')
            if answer == token: return
            if answer == 'EXIT': raise Stop('Stopped at your request; the step was not started.')
            print(f'  Please type {token} or EXIT. Enter does not confirm anything.', flush=True)

    def pause(self, flag, text, cmd=None):
        if getattr(self.a, flag): return
        if cmd: self.shell(cmd)
        if sys.stdin.isatty():
            self.log(text, detail=True)
            ui.action(text)
            while True:
                try: answer = input('  Your input → ').strip().upper()
                except EOFError: break
                if answer == 'RESUME':
                    self.identity()
                    return
                if answer == 'EXIT': break
                print('Please type RESUME or EXIT. Pressing Enter alone changes nothing.', flush=True)
        raise Stop(text + f'\nThen run the same command again with --{flag.replace("_", "-")} added.')

    def probe_temporary_root(self):
        for client in ('su', '/data/local/tmp/su'):
            try:
                out = self.shell(shlex.quote(client) + ' -c id', timeout=5, check=False)
            except Stop:
                continue
            if 'uid=0(' in out:
                self.temporary_su_client = client
                return True
        return False

    def temporary_su(self, command, **kwargs):
        client = getattr(self, 'temporary_su_client', 'su')
        return self.shell(shlex.quote(client) + ' -c ' + shlex.quote(command), **kwargs)

    def clear_ghostlock(self):
        self.state['pending'] = None
        self.state.pop('ghostlock_attempts', None)
        self.save()

    def resume_ghostlock(self):
        if self.state.get('pending') != 'ghostlock':
            return
        require(self.prop('sys.boot_completed') == '1' and not self.prop('ro.twrp.version'),
                'GhostLock resume requires booted Android; no flash or unlock will be repeated.')
        self.log('Resuming GhostLock: waiting for a working root service, not just the ROOTED marker.')
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if self.probe_temporary_root():
                self.clear_ghostlock()
                self.ghost_resume_authorized = True
                self.log('OK: Existing temporary root service verified; continuing without rerunning GhostLock.')
                return
            time.sleep(2)
        attempts = self.state.get('ghostlock_attempts', 1)
        require(isinstance(attempts, int) and 0 <= attempts < 2,
                'GhostLock already used both attempts; no further automatic exploit attempt.')
        self.log('Root service unavailable; a verified reboot will discard the temporary attempt before one retry.')
        self.reboot()
        self.state['pending'] = None
        self.state['ghostlock_attempts'] = attempts
        self.save()
        self.ghost_resume_authorized = True
        self.ghost_reboot_ready = True

    def ghost(self):
        if self.probe_temporary_root(): return
        used = self.state.get('ghostlock_attempts', 0)
        require(isinstance(used, int) and 0 <= used <= 2, 'Invalid GhostLock attempt counter.')
        for attempt in range(used + 1, 3):
            self.log(f'GhostLock: attempt {attempt}/2')
            if self.ghost_attempt(retry=self.state.get('pending') == 'ghostlock'): return
            if attempt == 1:
                self.log('No proof of root: retrying once after a verified reboot.')
        raise Stop('GhostLock failed after TWO attempts. No more automatic retries.')

    def ghost_attempt(self, retry=False):
        if getattr(self, 'ghost_reboot_ready', False):
            self.ghost_reboot_ready = False
        else:
            self.reboot()
        if retry:
            require(self.state.get('pending') == 'ghostlock', 'Unexpected checkpoint: GhostLock retry is blocked.')
            self.state['pending'] = None; self.save()
        self.shell('svc wifi disable')
        with zipfile.ZipFile(self.file('ghostlock-karat-v1.0.4.zip')) as z:
            preload = self.work / 'preload'
            preload.write_bytes(z.read('ghostlock-karat-v1.0.4/bin/preload'))
        self.push(preload, '/data/local/tmp/preload')
        self.state['pending'] = 'ghostlock'
        self.state['ghostlock_attempts'] = self.state.get('ghostlock_attempts', 0) + 1
        self.save()
        self.shell('chmod 755 /data/local/tmp/preload && rm -f /data/local/tmp/ghostlock.proof /data/local/tmp/ghostlock.log && (nohup /data/local/tmp/preload >/data/local/tmp/ghostlock.log 2>&1 </dev/null &)')
        end = time.monotonic() + 210
        next_log = time.monotonic() + 15
        waiting_for_service = False
        while time.monotonic() < end:
            time.sleep(3)
            proof = self.shell('cat /data/local/tmp/ghostlock.proof', check=False)
            if 'ROOTED' in proof:
                if self.probe_temporary_root():
                    self.shell('cat /data/local/tmp/ghostlock.log', check=False)
                    self.clear_ghostlock()
                    return True
                if not waiting_for_service:
                    self.log('ROOTED marker received; waiting for the su client and root daemon to become ready.')
                    waiting_for_service = True
            if time.monotonic() >= next_log:
                self.shell('cat /data/local/tmp/ghostlock.log', check=False)
                next_log = time.monotonic() + 30
        self.shell('cat /data/local/tmp/ghostlock.log', check=False)
        return False

    def unlock(self):
        require(shutil.disk_usage(self.base).free > 12 * 1024**3, 'The PC needs at least 12 GiB of free backup space before unlocking.')
        self.log('WARNING: Unlock writes the bootloader/IDME and can permanently brick the device. Stable power and USB are required.')
        self.confirm('UNLOCK', 'The next step unlocks the bootloader and writes IDME data. Keep USB and power connected.')
        self.ghost()
        with zipfile.ZipFile(self.file('amonet-karat-v1.3.0.zip')) as z:
            binary = self.work / 'unlock'; binary.write_bytes(z.read('amonet/bin/unlock'))
        require('uid=0(' in self.temporary_su('id'), 'Temporary root has been lost.')
        self.push(binary, '/data/local/tmp/unlock')
        self.shell('chmod 755 /data/local/tmp/unlock')
        self.state['pending'] = 'unlock'; self.save()
        # Same binary invocation as upstream unlock.sh. A reboot may terminate ADB.
        out = self.temporary_su('/data/local/tmp/unlock', timeout=180, check=False)
        require('Unlock OK' in out, 'Unlock OK is missing; no automatic retry!')
        time.sleep(5); self.wait(True)

    def backups(self):
        require(self.prop('ro.twrp.version') == '3.7.1_12-0', 'Backup is allowed only in TWRP.')
        self.recovery_ready()
        require(not self.backup.exists(), f'Backup destination exists without a completed checkpoint: {self.backup}; it was not overwritten.')
        self.shell('df -h /data /sdcard')
        require(shutil.disk_usage(self.base).free > 12 * 1024**3, 'The PC needs at least 12 GiB of free backup space.')
        for spec, label, words in [('BD', 'auto-before-persistent-root', ['Boot', 'Data']), ('S', 'auto-before-post-ota', ['System'])]:
            self.recovery_backup(spec, label, words)
        self.backup.mkdir(parents=True)
        self.adb('pull', f'/sdcard/TWRP/BACKUPS/{self.serial}', str(self.backup / 'twrp'), timeout=1800)
        self.shell('[ -b /dev/block/mapper/vendor ] || lptools map vendor')
        size = int(self.shell('blockdev --getsize64 /dev/block/mapper/vendor'))
        require(size > 0, 'Empty vendor device.')
        dest = self.backup / 'vendor-before-post-ota.img'
        self.log('Reading the vendor partition to the PC as binary data (no device write).')
        with open(dest, 'wb') as f:
            try:
                p = subprocess.run(['adb', '-s', self.serial, 'exec-out', 'cat /dev/block/mapper/vendor'], stdout=f, stderr=subprocess.PIPE, timeout=300)
            except subprocess.TimeoutExpired: raise Stop('Vendor backup timeout.')
        require(p.returncode == 0 and dest.stat().st_size == size, 'Vendor backup is incomplete.')
        require(sha(dest) == self.shell('sha256sum /dev/block/mapper/vendor').split()[0], 'Vendor backup hash mismatch.')
        # Verify the transferred TWRP backup archives, not just adb pull's exit code.
        verified = {}
        for label in ('auto-before-persistent-root', 'auto-before-post-ota'):
            remote = f'/sdcard/TWRP/BACKUPS/{self.serial}/{label}'
            listing = self.shell('find ' + remote + ' -type f -name "*.win*" ! -name "*.sha2" ! -name "*.md5" -exec sha256sum {} \\;')
            require(listing, 'No TWRP backup data found.')
            for line in listing.splitlines():
                digest, rel = line.split(None, 1)
                local = self.backup / 'twrp' / label / Path(rel).name
                require(local.is_file() and sha(local) == digest, f'Backup transfer is corrupted: {local}')
                verified[local.relative_to(self.backup).as_posix()] = digest
        verified[dest.name] = sha(dest)
        atomic_json(self.backup / 'verified.json', {'serial': self.serial, 'fingerprint': self.state['profile']['fingerprint'], 'files': verified})

    def verify_backups(self):
        require((self.backup / 'verified.json').exists(), 'Verified PC backup is missing.')
        manifest = json.loads((self.backup / 'verified.json').read_text(encoding='utf-8'))
        require(manifest.get('serial') == self.serial and manifest.get('files'), 'Backup manifest does not match the device.')
        require(manifest.get('fingerprint') and manifest.get('fingerprint') in (self.state.get('profile', {}).get('fingerprint'), self.update_backup_fingerprint()), 'Backup firmware does not match.')
        require('vendor-before-post-ota.img' in manifest['files'], 'Vendor backup is missing.')
        normalized = {}
        for rel, digest in manifest['files'].items():
            # Old Windows manifests used backslashes; use portable paths for
            # validation and prefix matching without changing the saved hashes.
            require(isinstance(rel, str), 'Invalid backup path.')
            portable = rel.replace('\\', '/')
            relative = Path(portable)
            path = self.backup / relative
            require(not relative.is_absolute() and not re.match(r'^[A-Za-z]:', portable) and '..' not in relative.parts and path.resolve().is_relative_to(self.backup.resolve()), 'Invalid backup path.')
            require(portable not in normalized, 'Ambiguous backup path.')
            require(path.is_file() and sha(path) == digest, f'PC backup is missing or has changed: {rel}')
            normalized[portable] = digest
        for prefix in ('twrp/auto-before-persistent-root/boot.', 'twrp/auto-before-persistent-root/data.', 'twrp/auto-before-post-ota/system.'):
            require(any(name.startswith(prefix) for name in normalized), f'Boot/Data/System backup is incomplete: {prefix}')
        self.log('PC BACKUPS: Serial number, firmware and all SHA256 hashes rechecked.')

    def postota(self):
        self.verify_backups()
        self.shell('[ -b /dev/block/mapper/system ] || lptools map system')
        self.shell('mkdir -p /mnt/postota-check; mount -t ext4 -o ro,noload /dev/block/mapper/system /mnt/postota-check')
        try:
            for offset, count, expected in [(610743,1,'dd'),(610760,1,'01'),(494270,4,'4a ea 07 05')]:
                out = self.shell(f'dd if=/mnt/postota-check/system/apex/com.android.adbd/bin/adbd bs=1 skip={offset} count={count} 2>/dev/null | od -An -tx1')
                require(' '.join(out.split()) == expected, f'adbd byte check {offset} failed. No Post-OTA flash.')
        finally: self.shell('umount /mnt/postota-check')
        self.flash('post-ota-karat-v1.0.0.zip', '- info done')

    def magisk_flash(self):
        self.verify_backups()
        if not self.prop('ro.twrp.version'): self.reboot(True)
        self.flash('Magisk-v30.7.apk', '- Done')

    def module(self, name, markers=()):
        self.root_ok()
        dest = '/sdcard/google-play/' + Path(name).name
        self.shell('mkdir -p /sdcard/google-play')
        self.push(self.file(name), dest)
        out = self.shell('magisk --install-module ' + dest, timeout=300)
        require('Done' in out and not re.search(r'\b(abort|failed|error)\b', out, re.I) and all(m in out for m in markers), 'Magisk module installation is incomplete.')

    def root_flow(self):
        phase = self.a.root_phase
        if self.a.core_only: phase = 'permanent'
        if phase == 'temporary':
            names = ['ghostlock-karat-v1.0.4.zip']
        elif phase == 'google':
            names = [n for n in FILES if n.startswith('google-play/')]
        else:
            names = ['amonet-karat-v1.3.0.zip', 'ghostlock-karat-v1.0.4.zip', 'post-ota-karat-v1.0.0.zip', 'Magisk-v30.7.apk']
            if phase == 'all': names += [n for n in FILES if n.startswith('google-play/')]
        if getattr(self.a, 'update', False) or phase == 'update':
            names += [FIRMWARE, 'google-play/vector.zip']
        self.prepare(list(dict.fromkeys(names)))
        if self.a.prepare_only: return
        self.connect()
        if getattr(self.a, 'update', False) or phase == 'update':
            self.resume_ghostlock()
            from firmware_update import FINGERPRINT
            already_current = not self.state.get('firmware_update') and self.state['profile']['fingerprint'] == FINGERPRINT
            if already_current:
                self.log('Fire OS 8.1.8.2 is already installed; skipping the firmware flash.')
                if phase == 'update': return
            else:
                self.update_flow()
                if phase != 'all': return
        if phase in ('temporary', 'permanent', 'all'): self.resume_ghostlock()
        if phase == 'temporary':
            self.temporary_root()
            self.root_cleanup('temporary')
            return
        if phase in ('permanent', 'all'):
            self.permanent_root()
            self.stage('permanent-cleanup', lambda: self.root_cleanup('permanent'))
            self.log('OK: PERMANENT ROOT with Magisk completed.')
        if phase in ('google', 'all'):
            require(not self.state.get('pending'), 'Uncertain write operation; Google setup is blocked.')
            require(self.prop('sys.boot_completed') == '1' and not self.prop('ro.twrp.version'), 'Google setup requires fully booted Android.')
            self.root_ok()
            require('30.7:' in self.shell('magisk -v'), 'Complete permanent root with Magisk 30.7 first.')
            self.google_flow()
            self.stage('google-cleanup', lambda: self.root_cleanup('google'))
            self.log('ROOT/FRAMEWORK COMPLETE. microG: enable Device registration and Cloud Messaging; sign in to Google yourself.')

    def restore_wifi(self):
        """Restore connectivity only in Android, after rechecking the OTA block."""
        self.log('Restoring Wi-Fi after root setup…')
        try:
            if self.prop('ro.twrp.version') or self.prop('sys.boot_completed') != '1':
                self.log('WARNING: Wi-Fi restoration deferred until Android is fully booted.')
                return False
            disabled = set(self.shell('pm list packages -d --user 0').splitlines())
            ota = {'package:com.amazon.device.software.ota', 'package:com.amazon.device.software.ota.override'}
            if not ota <= disabled:
                self.log('WARNING: Both OTA packages are not confirmed disabled; Wi-Fi will not be enabled automatically.')
                return False
            self.shell('svc wifi enable')
            end = time.monotonic() + 15
            while time.monotonic() < end:
                if self.shell('settings get global wifi_on') == '1':
                    self.log('OK: Wi-Fi enabled; both OTA update packages remain disabled.')
                    return True
                time.sleep(1)
        except Stop as error:
            self.log(f'WARNING: Could not restore Wi-Fi automatically: {error}')
        self.log('WARNING: Wi-Fi could not be confirmed enabled. Setup will continue; enable Wi-Fi in Fire TV settings if needed.')
        return False

    def temporary_root(self):
        require(not self.state.get('pending'), 'Uncertain write operation; temporary root is blocked.')
        require(self.prop('sys.boot_completed') == '1' and not self.prop('ro.twrp.version'), 'Temporary root requires Android.')
        if not self.probe_temporary_root():
            if not getattr(self, 'ghost_resume_authorized', False):
                self.confirm('ROOT', 'Obtain temporary root and disable OTA updates.')
            self.ghost()
        require('uid=0(' in self.temporary_su('id'), 'Temporary root is unavailable.')
        for package in ('com.amazon.device.software.ota', 'com.amazon.device.software.ota.override'):
            out = self.temporary_su('pm disable --user 0 ' + package)
            require(out.rstrip().endswith('new state: disabled'), 'OTA blocking is not confirmed: ' + package)
        out = self.shell('pm list packages -d --user 0')
        disabled = set(out.splitlines())
        require({'package:com.amazon.device.software.ota', 'package:com.amazon.device.software.ota.override'} <= disabled, 'Both OTA packages must be disabled.')
        self.restore_wifi()
        self.log('OK: Temporary root is available; OTA packages are disabled. Root itself is lost on reboot.')

    def resume_postota_preflight(self):
        """Recover an old false pending only from a complete, known pre-write log."""
        if self.state.get('pending') != 'postota':
            return
        self.active_stage = 'postota'
        # This source version logs every command before running it and sets
        # pending too early. Other versions require individual log inspection.
        known_source = 'd30fef3c2ee17dc4c2a57865fd984664775a156f2c918af8511bebde153abc87'
        evidence = None
        current = Path(self.logfile.name).resolve()
        for path in sorted(self.work.glob('*-root.log'), reverse=True):
            if path.resolve() == current:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except (OSError, UnicodeError):
                continue
            lines = text.splitlines()
            starts = [i for i, line in enumerate(lines)
                      if re.fullmatch(r'\[[^]\n]+\] START: postota', line)]
            if not starts:
                continue
            block = '\n'.join(lines[starts[-1]:])
            # Logs are shared across devices: require at least one command for
            # this serial and reject mixed-device stage output.
            serials = re.findall(r'^\[[^]\n]+\] \$ adb -s ([A-Za-z0-9_-]+) ', text, re.M)
            if not serials or self.serial not in serials:
                continue
            abort = re.search(r'^\[[^]\n]+\] STOP: Stufe=postota; Pending=postota; (.+)$', block, re.M)
            known = '; Skript-SHA256=' + known_source in text
            # Known source logs every installer command before running it.
            # Require an explicit abort; truncated logs cannot prove no write.
            rejected = abort is not None
            if known and set(serials) == {self.serial} and rejected and 'twrp install' not in block and 'Installer meldet' not in abort.group(1):
                evidence = path
            if evidence is None:
                self.log('Original Post-OTA log: ' + str(path))
                if abort:
                    self.log('Original error: ' + abort.group(1))
            break  # Never fall back to an older attempt after an ambiguous one.
        if evidence is None:
            self.log('WARNING: Post-OTA status is uncertain. Pending is preserved; no repeat flash.')
            self.log('The earlier root log containing START: postota and the original error is needed — not just the log of this resume attempt.')
            self.log('Log folder: ' + str(self.work))
            return
        require(self.prop('ro.twrp.version') == '3.7.1_12-0',
                'Preflight was aborted, but TWRP is not active. Boot into TWRP first; the checkpoint is preserved.')
        self.verify_backups()
        saved = self.statefile.with_suffix('.json.before-postota-resume')
        if not saved.exists():
            shutil.copy2(self.statefile, saved)
        self.state['pending'] = None
        self.save()
        self.log('OK: Earlier log confirms preflight aborted; no flash started. Checkpoint backed up; preflight will run again.')
        self.log('Evidence: ' + str(evidence))
        self.active_stage = None

    def permanent_root(self):
        self.resume_postota_preflight()
        # Only unambiguous completed unlock may be recovered automatically.
        if self.state.get('pending') == 'unlock' and self.prop('ro.twrp.version') == '3.7.1_12-0': self.finish('unlock')
        require(not self.state.get('pending'), f'Uncertain write operation: {self.state.get("pending")}. Check the log; do not flash again.')
        if 'unlock' not in self.state['done'] and 'uid=0(' in self.shell('id') and '30.7:' in self.shell('magisk -v', check=False):
            # Adopt existing finished installation without flashing it again.
            require(self.a.adopt_existing, 'Already rooted: use --adopt-existing; do not unlock again.')
            self.log('Existing root installation: checking TWRP before adoption.')
            self.verifying_existing = True
            self.reboot(True)
            for stage in ['unlock', 'backup', 'postota', 'postota-boot', 'magisk', 'magisk-boot']: self.finish(stage)
            self.reboot()
            self.verifying_existing = False
        if 'unlock' not in self.state['done']:
            require('uid=0(' not in self.shell('id'), 'Unknown rooted installation without Magisk 30.7; no automatic repeat unlock.')
        self.stage('unlock', self.unlock)
        self.stage('backup', self.backups)
        self.stage('postota', self.postota)
        self.stage('postota-boot', lambda: (self.reboot(), self.root_ok()))
        self.restore_wifi()
        self.stage('magisk', self.magisk_flash, risky=True)
        self.stage('magisk-boot', lambda: (self.reboot(), self.root_ok()))
        require('30.7:' in self.shell('magisk -v'), 'Magisk is not version 30.7.')
        if 'magisk-ui' not in self.state['done']:
            self.magisk_app()
            self.finish('magisk-ui')
        self.stage('magisk-setup-boot', self.magisk_setup_reboot)
        self.ensure_preinit()

    def magisk_setup_reboot(self):
        self.log('Magisk setup completed: rebooting the Stick automatically. Keep USB and power connected.')
        self.reboot()
        self.root_ok()
        require('30.7:' in self.shell('magisk -v'), 'Magisk is not version 30.7.')
        self.verify_magisk_app(self.file('Magisk-v30.7.apk'))

    def open_microg_settings(self):
        self.log('Opening microG settings on the TV…')
        components = []
        for category in ('android.intent.category.LAUNCHER', 'android.intent.category.LEANBACK_LAUNCHER'):
            out = self.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c ' + category + ' com.google.android.gms', check=False)
            components.extend(line.strip() for line in out.splitlines()
                              if re.fullmatch(r'com\.google\.android\.gms/[A-Za-z0-9_.$]+', line.strip()))
        components.append('com.google.android.gms/org.microg.gms.ui.SettingsActivity')
        for component in dict.fromkeys(components):
            out = self.shell('am start -W -n ' + shlex.quote(component), check=False)
            if ('Status: ok' in out or 'Starting: Intent' in out) and not re.search(r'error|exception|unable|denial', out, re.I):
                self.log('OK: microG settings opened. Select Self-Check on the TV.')
                return
        self.log('WARNING: Could not open microG automatically. Open microG Settings on the TV, then Self-Check; return here when ready.')

    def ensure_builtin_zygisk_off(self):
        query = "SELECT COALESCE((SELECT value FROM settings WHERE key='zygisk'),0) AS enabled;"
        changed = False
        while True:
            out = self.shell('magisk --sqlite ' + shlex.quote(query))
            require(out in ('enabled=0', 'enabled=1'), 'Cannot determine the Magisk built-in Zygisk setting; no framework modules were installed.')
            if out == 'enabled=0':
                if changed:
                    self.reboot()
                    self.root_ok()
                self.log('OK: Magisk built-in Zygisk is OFF; continuing automatically. Zygisk Next handles it.')
                return
            out = self.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.topjohnwu.magisk')
            components = [line.strip() for line in out.splitlines() if re.fullmatch(r'com\.topjohnwu\.magisk/[A-Za-z0-9_.$]+', line.strip())]
            require(len(components) == 1, 'Cannot open Magisk. Disable built-in Zygisk in Magisk settings, then restart the main setup.')
            old = self.a.zygisk_off
            self.a.zygisk_off = False
            try:
                self.pause('zygisk_off', 'Magisk built-in Zygisk is ON. In Magisk settings, turn Zygisk OFF, then type RESUME. The script will check the setting and reboot before installing the framework.', 'am start -W -n ' + shlex.quote(components[0]))
            finally:
                self.a.zygisk_off = old
            changed = True

    def google_flow(self):
        if 'framework' not in self.state['done']:
            self.ensure_builtin_zygisk_off()
        self.ensure_preinit()
        self.stage('framework', lambda: (self.module('google-play/zygisk-next.zip'), self.module('google-play/vector.zip')), risky=True)
        if 'framework-boot' not in self.state['done']: self.verify_vector_policy()
        self.stage('framework-boot', lambda: self.reboot())
        self.stage('fakegapps-install', lambda: self.install('google-play/fakegapps.apk'))
        if 'fakegapps-scope' not in self.state['done']:
            self.pause('fakegapps_ready', 'Vector: enable FakeGApps and scope it ONLY to System Framework / android. No manual reboot is needed.', VECTOR)
            self.finish('fakegapps-scope')
        self.stage('fakegapps-boot', lambda: self.reboot())
        self.stage('google-apks', lambda: (self.install('google-play/microg.apk'), self.install('google-play/play-store-tv.apk'), self.verifier()))
        if 'spoof-check' not in self.state['done']:
            if not self.a.spoof_ready: self.open_microg_settings()
            self.pause('spoof_ready', 'In microG, open Self-Check and check that System spoofs signature is checked. Then type RESUME here.')
            self.finish('spoof-check')
        self.stage('microg-promotion', lambda: (self.verifier(), self.module('google-play/microg-installer.zip', ('GmsCore promoted','Vending promoted'))), risky=True)
        self.stage('microg-boot', self.microg_reboot)

    def microg_reboot(self):
        self.verifier()
        self.reboot()
        self.verifier()

    def verifier_repair(self):
        self.connect()
        require(not self.state.get('pending'), 'Uncertain write operation; check the log first.')
        self.root_ok()
        module = '/data/adb/modules/microg_installer_revived_again'
        require(self.shell(f'test -f {module}/module.prop && echo OK') == 'OK', 'microG module is missing.')
        self.shell(f'touch {module}/disable && sync')
        self.reboot()
        self.verifier()
        self.shell(f'rm {module}/disable && sync')
        self.reboot()
        self.verifier()
        self.finish('microg-boot')
        self.log('OK: manuelle Verifier-Reparatur abgeschlossen. Danach 03_google_play_and_microg erneut starten.')

    def boot_help(self):
        serial = self.serial or 'SERIAL_NUMBER'
        self.log('BOOT HELP: Android has not confirmed boot completion after 6 minutes. A verifier conflict is possible but not yet confirmed.')
        self.log('Check ADB: adb devices -l; if the device is missing, check the connection; do not flash again.')
        self.log(f'Check crashes: adb -s {serial} logcat -b crash -d -t 120')
        self.log('If the crash says "There must be exactly one verifier" and root ADB is reachable:')
        self.log(f'python karat-automation/karat.py root --base . --serial {serial} --repair-verifier')
        self.log('This explicitly requested repair: disable the microG module → reboot → disable/check Google verifier → enable module → reboot → check.')
        self.log('If the log instead reports xposed_file or dex2oat permission errors, keep Vector disabled and check Magisk preinit; see UPDATE.md. A verifier repair alone cannot fix missing SELinux rules.')
        self.log('Alternatively, individual manual ADB commands are in MANUAL-REPAIR.md. Preserve checkpoints.')

    def root_cleanup(self, phase='all'):
        if phase == 'temporary':
            # GhostLock uses /data/local/tmp, not sdcard. Its su daemon may still run.
            self.log('OK: The temporary-root phase placed no files on /sdcard; nothing to delete there.')
            return
        permanent = ['/sdcard/Magisk-v30.7.zip', '/sdcard/Magisk-v30.7.apk', '/sdcard/post-ota-karat-v1.0.0.zip']
        google = ['/sdcard/google-play/' + Path(name).name for name in FILES if name.startswith('google-play/')]
        if phase in ('permanent', 'all'):
            self.cleanup()
        files = permanent if phase == 'permanent' else google if phase == 'google' else permanent + google
        command = 'set -e\nfor f in ' + ' '.join(shlex.quote(path) for path in files) + '; do\nif [ -f "$f" ]; then rm -f "$f"; echo "Deleted: $f"; fi\ndone\n'
        if phase in ('permanent', 'all'):
            command += f'for d in /sdcard/TWRP/BACKUPS/{self.serial} /sdcard/TWRP/BACKUPS /sdcard/TWRP; do if [ -d "$d" ]; then rmdir "$d" 2>/dev/null || :; fi; done\n'
        if phase in ('google', 'all'):
            command += r"""if [ -d /sdcard/google-play ]; then rmdir /sdcard/google-play 2>/dev/null || :; fi
if [ -d /sdcard/Download/Downloader ]; then
    find /sdcard/Download/Downloader -type f \( -name "*.apk" -o -name "*.apkm" \) -exec rm -f {} \;
fi
"""
        self.shell(command)
        self.log(f'OK: Temporary /sdcard files for phase {phase} cleaned up; PC backups are preserved.')

    def verifier(self):
        out = self.shell('pm disable --user 0 com.android.vending/com.google.android.finsky.verifier.impl.PackageVerificationReceiver')
        require(out.rstrip().endswith('new state: disabled'), 'Google verifier is not disabled.')
        out = self.shell('cmd package query-receivers --brief --user 0 -a android.intent.action.PACKAGE_NEEDS_VERIFICATION -t application/vnd.android.package-archive')
        require(re.search(r'^1 receivers found:\s*$', out, re.M) and 'com.amazon.adep/.nimh.receiver.PackageVerificationReceiver' in out and 'com.android.vending/' not in out, 'Verifier conflict: promotion/reboot blocked.')
        self.log('OK: Google verifier disabled · only Amazon verifier remains active.')

    def setting(self, namespace, key, value):
        self.shell(f'settings --user 0 put {namespace} {key} {value}')
        require(self.shell(f'settings --user 0 get {namespace} {key}') == str(value), f'Setting {key} was not applied.')

    def write_device(self, destination, content, mode='700'):
        require(destination.startswith('/data/adb/service.d/'), 'Invalid script destination path')
        local = self.work / Path(destination).name
        local.write_text(content, encoding='utf-8')
        temp = '/data/local/tmp/karat-' + local.name
        self.push(local, temp)
        self.shell(f'mkdir -p /data/adb/service.d; if [ -f {destination} ] && [ ! -f {destination}.before-automation ]; then cp -p {destination} {destination}.before-automation; fi; cp {temp} {destination}.new && chmod {mode} {destination}.new && mv {destination}.new {destination} && rm {temp}')

    def migrate_clock(self):
        # The replacement has a new package ID and signing certificate. Remove
        # only the obsolete clock helper; launcher data and settings are kept.
        legacy = 'local.karat.emotnclock'
        if self.shell('pm path ' + legacy, check=False).startswith('package:'):
            self.log('Replacing the fixed Berlin clock helper with Emotn System Clock.')
            out = self.shell('pm uninstall ' + legacy)
            require('Success' in out, 'Could not remove the obsolete clock helper; do not enable both clock modules.')
            require(not self.shell('pm path ' + legacy, check=False).startswith('package:'), 'The obsolete clock helper is still installed.')

    def emotn_flow(self):
        names = ['EmotnUI.apk', 'Amazon-Appstore-Direct.apk', 'FireTV-Settings-Bridge.apk', 'Emotn-System-Clock.apk', 'Emotn-Idle-Timer.apk', 'Emotn-App-Categories.apk']
        self.prepare(names)
        if self.a.prepare_only: return
        self.connect(); self.root_ok()
        require('30.7:' in self.shell('magisk -v'), 'Magisk 30.7 is missing.')
        with zipfile.ZipFile(self.file('google-play/vector.zip')) as z:
            module_id = re.search(r'^id=([A-Za-z0-9_.-]+)\s*$', z.read('module.prop').decode(), re.M)
        require(module_id, 'Invalid Vector module.prop.')
        module_path = '/data/adb/modules/' + module_id.group(1)
        require(self.shell(f'test -f {module_path}/module.prop && test ! -f {module_path}/disable && echo OK') == 'OK', 'Active Vector module is missing; complete root setup including the framework first.')
        # Save reversible state before changing launcher/settings; never overwrite first snapshot.
        self.stage('emotn-snapshot', self.emotn_snapshot)
        self.stage('emotn-clock-migration', self.migrate_clock)
        for name in names: self.stage('app-' + Path(name).stem, lambda n=name: self.install(n))
        self.stage('emotn-home', self.home)
        self.stage('emotn-settings', lambda: (self.setting('secure','amazon_ambient_enabled',0), self.setting('secure','screensaver_enabled',0), self.setting('secure','sleep_timeout',4200000), self.setting('system','time_12_24',24)))
        self.stage('emotn-startup', lambda: self.write_device('/data/adb/service.d/emotn-home.sh', '#!/system/bin/sh\nwhile [ "$(/system/bin/getprop sys.boot_completed)" != "1" ]; do sleep 2; done\nsleep 15\n/system/bin/am force-stop com.oversea.aslauncher\n/system/bin/am start --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME -n '+HOME+'\n'))
        self.stage('wifi-adb-policy', self.wifi_policy)
        if any(stage not in self.state['done'] for stage in ('emotn-system-clock-scope', 'emotn-categories-scope')):
            self.pause('emotn_ready', 'Vector: enable Emotn System Clock, Idle Timer and App Categories, scoped ONLY to Emotn UI. The clock follows the Fire TV timezone automatically, including changes. Emotn: set your own town for weather, keep the video wallpaper, set the screensaver to 10 minutes; select Always for Settings Bridge in the chooser if needed.', VECTOR)
            self.finish('emotn-scope')
            self.finish('emotn-system-clock-scope')
            self.finish('emotn-categories-scope')
        self.log('Clock timezone: follows the Fire TV setting (' + self.prop('persist.sys.timezone') + '); no timezone is forced.')
        self.shell('am force-stop com.oversea.aslauncher')
        self.shell('am start -n ' + HOME)
        self.stage('emotn-compile', lambda: self.compile('com.oversea.aslauncher'))
        self.log('EMOTN COMPLETE. No device reboot is needed. Check Vector logs: 1200 us → 1200 ms; try Home/Settings/Appstore. The boot script takes effect on the next regular reboot.')

    def home(self):
        out = self.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME -p com.oversea.aslauncher')
        require(HOME in out, 'Emotn HOME component does not match.')
        self.shell('am start -W -n ' + HOME)
        self.pause('launcher_ready', 'On the TV, use the remote to grant EmotnUI the permissions it requests. Then check that the display and remote navigation work. Once done, type RESUME here to continue changing the home launcher.')
        require('package:' in self.shell('pm path com.amazon.firehomestarter'), 'firehomestarter is missing.')
        for cmd, marker in [('pm disable --user 0 com.amazon.firehomestarter','new state: disabled'), ('pm enable --user 0 com.amazon.tv.launcher','new state: enabled'), ('pm disable --user 0 com.amazon.tv.launcher/.ui.HomeActivity_vNext','new state: disabled'), ('cmd package set-home-activity --user 0 '+HOME,'Success')]:
            require(marker in self.shell(cmd), 'Home launcher change failed; see rollback-home.sh.')
        self.shell('am force-stop com.amazon.tv.launcher')
        self.shell('am start -n ' + HOME)
        require(HOME in self.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'), 'HOME resolution is incorrect.')

    def emotn_snapshot(self):
        snap = {'serial':self.serial, 'settings':{}, 'launcher': self.shell('dumpsys package com.amazon.tv.launcher'), 'starter':self.shell('dumpsys package com.amazon.firehomestarter')}
        for ns, key in [('secure','amazon_ambient_enabled'),('secure','screensaver_enabled'),('secure','sleep_timeout'),('system','time_12_24')]:
            snap['settings'][ns + ':' + key] = self.shell(f'settings --user 0 get {ns} {key}')
        atomic_json(self.work / f'{self.serial}-emotn-before.json', snap)

    def wifi_policy(self):
        self.write_device('/data/adb/service.d/karat-wifi-adb.sh', '#!/system/bin/sh\n/data/adb/magisk/magiskpolicy --live "allow netd su fd use" "allow netd su tcp_socket { read write getopt setopt }"\n')
        self.shell('sh /data/adb/service.d/karat-wifi-adb.sh')

    def compile(self, package):
        require('Success' in self.shell('cmd package compile -m speed -f ' + package, timeout=600), 'App compilation failed.')

    def diagnostics(self):
        if not self.serial: return
        self.log('Read-only diagnostics after an uncertain write/boot state:')
        for command in ['getprop sys.boot_completed; getprop ro.twrp.version; id', 'cat /tmp/recovery.log', 'logcat -d -t 300']:
            try: self.shell(command, timeout=8, check=False)
            except (Stop, OSError): pass

    def cleanup(self):
        self.verify_backups()
        # Only the two directories created by THIS automation, not arbitrary TWRP/download files.
        for label in ('auto-before-persistent-root','auto-before-post-ota'):
            self.shell(f'rm -rf /sdcard/TWRP/BACKUPS/{self.serial}/{label}')
        self.log('Only the two setup-owned, verified TWRP backups were removed from the device. PC backups are preserved.')

def parser():
    entry = {'root':'Root phase', 'emotn':'04_emotn-launcher-setup'}.get(sys.argv[1] if len(sys.argv)>1 else '', 'karat.py')
    p = argparse.ArgumentParser(prog=entry, usage='%(prog)s [options]', description='Supported karat profiles; USB; checkpoints; no blind retries of flash operations.')
    p.add_argument('flow', choices=['root','emotn'], help=argparse.SUPPRESS)
    p.add_argument('--lang', choices=['en','de'], help='Interface language; selected before setup')
    p.add_argument('--base', default=str(HERE.parent), help='File directory; default: parent folder of karat-automation')
    p.add_argument('--serial')
    p.add_argument('--verbose', action='store_true', help='Also show technical commands and full tool output in the terminal')
    p.add_argument('--root-phase', choices=['temporary','permanent','google','all','update'], default='all', help='Root subphase; default: all root phases')
    p.add_argument('--update', action='store_true', help='Integrate Fire OS 8.1.8.2 into permanent root')
    p.add_argument('--dry-run', action='store_true', help='Download/check files and simulate output; no device required')
    p.add_argument('--preview-only', action='store_true', help='Simulate output only; no downloads or files')
    p.add_argument('--dry-run-scenario', choices=['success','boot-timeout'], default='success', help='Preview scenario (with --dry-run or --preview-only)')
    p.add_argument('--repair-verifier', action='store_true', help='Explicitly requested verifier repair with two reboots')
    p.add_argument('--aapt', help='Path to aapt or aapt2 from Android SDK Build Tools')
    p.add_argument('--prepare-only', action='store_true', help='File checks/downloads only; no device changes')
    p.add_argument('--adopt-existing', action='store_true', help='Check and adopt existing root/TWRP without flashing again')
    p.add_argument('--core-only', action='store_true', help='Root without Google/Vector; Emotn hooks require the framework afterward')
    for flag in ['magisk-ready','zygisk-off','fakegapps-ready','spoof-ready','launcher-ready','emotn-ready','categories']:
        p.add_argument('--'+flag, action='store_true')
    return p

def main():
    s = None
    try:
        args = parser().parse_args()
        require(not args.update or (args.flow == 'root' and args.root_phase in ('permanent','all','update')), '--update requires permanent root or the update phase.')
        require(not (args.dry_run and args.preview_only), 'Do not combine --dry-run and --preview-only.')
        if args.preview_only:
            from dry_run import preview
            return preview(args.flow, args.dry_run_scenario, phase='update' if args.update else args.root_phase)
        require(args.dry_run or args.dry_run_scenario == 'success', '--dry-run-scenario requires --dry-run or --preview-only.')
        if args.dry_run:
            require(not args.repair_verifier, 'Repair is not a dry run.')
            args.prepare_only = True
            s = Setup(args)
            s.log('DRY RUN: Real downloads/file checks; no ADB or device changes.')
            if args.flow == 'root': s.root_flow()
            else: s.emotn_flow()
            from dry_run import preview
            return preview(args.flow, args.dry_run_scenario, downloads=True, phase='update' if args.update else args.root_phase)
        s = Setup(args)
        if s.a.repair_verifier: s.verifier_repair()
        elif s.a.flow == 'root': s.root_flow()
        else: s.emotn_flow()
        return 0
    except (Stop, OSError, ValueError, zipfile.BadZipFile) as e:
        if s:
            s.log(f'STOP: Stage={s.active_stage}; Pending={s.state.get("pending")}; {e}')
            s.logfile.write(traceback.format_exc())
            s.log(f'Debug log: {s.logfile.name}')
            if 'Boot timeout' in str(e) and (s.active_stage == 'microg-boot' or (s.active_stage or '').startswith(UPDATE_PREFIX)): s.boot_help()
            if s.state.get('pending') or 'Boot timeout' in str(e): s.diagnostics()
        else: print('STOP:', e, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        if s: s.log('Cancelled. Keep device power/USB connected; check the checkpoint and log.')
        return 130
    finally:
        if s:
            s.logfile.close()
            s.lock.close()

if __name__ == '__main__': sys.exit(main())
