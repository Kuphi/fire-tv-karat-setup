"""Human-readable console output; full technical logging remains in the engine."""
import os
import re
import sys

TITLES={
 'emotn-clock-migration':'Replace obsolete fixed-zone clock helper',
 'temporary-root':'Temporary root and OTA blocking', 'unlock':'Unlock the bootloader',
 'backup':'One-time backup', 'postota':'Install Post-OTA',
 'postota-boot':'Boot Android after Post-OTA', 'magisk':'Flash Magisk',
 'magisk-boot':'Boot Android with Magisk', 'magisk-ui':'Set up the full Magisk app',
 'magisk-setup-boot':'Restart after Magisk setup and verify root',
 'framework':'Install Zygisk Next and Vector', 'framework-boot':'Restart the framework',
 'fakegapps-install':'Install FakeGApps', 'fakegapps-boot':'Restart with FakeGApps',
 'google-apks':'Install microG and Google Play', 'microg-promotion':'Promote microG and Play Store to privileged apps',
 'microg-boot':'Check the Google verifier and boot Android',
 'permanent-cleanup':'Clean up temporary root files', 'google-cleanup':'Clean up temporary Google files',
 'root-cleanup':'Clean up temporary setup files', 'emotn-snapshot':'Save the launcher state',
 'emotn-home':'Set Emotn as the home screen', 'emotn-settings':'Apply launcher settings',
 'emotn-startup':'Set up automatic launcher startup', 'wifi-adb-policy':'Set up ADB permissions',
 'emotn-compile':'Optimize Emotn', 'emotn-startup':'Set up automatic launcher startup',
}

def color(text,code):
    if sys.stdout.isatty() and not os.environ.get('NO_COLOR') and os.environ.get('TERM')!='dumb':
        return f'\033[{code}m{text}\033[0m'
    return text

def title(text,subtitle=None):
    print('\n'+color('━'*64,'36'),flush=True)
    print(color('  '+text,'1;36'),flush=True)
    if subtitle:print('  '+subtitle,flush=True)
    print(color('━'*64,'36')+'\n',flush=True)

def section(text):
    print('\n'+color('  ▶ '+text,'1;36'),flush=True)
    print('  '+'─'*58,flush=True)

def info(text):
    for line in str(text).splitlines():print('  '+line,flush=True)

def action(text,choices=None):
    title('YOUR INPUT IS REQUIRED')
    info(text)
    print('',flush=True)
    for token,meaning in choices or [('RESUME','done / continue'),('EXIT','exit safely')]:
        print('  '+color(f'{token:<10}','1;33')+' '+meaning,flush=True)
    info('\nPressing Enter alone does not confirm anything.')
    print('',flush=True)

def menu(rows):
    for number,label,description in rows:
        print('  '+color(f'[{number}]','1;33')+'  '+color(label,'1'),flush=True)
        if description:info('     '+description)
    print('',flush=True)

def event(text,detail=False,verbose=False):
    if verbose:
        print(text,flush=True);return
    if detail:return
    if text.startswith(('HOST:','APK:','COMMAND FINISHED:','EXIT:','$ ')):return
    if text.startswith('LOG:'):
        path=text[5:].split('; Mode=',1)[0]
        info('Full technical log: '+path);return
    if text.startswith('FILE CHECK:'):
        info(color('… '+text.split(':',1)[1].strip(),'36'));return
    if text.startswith('FILE:'):
        name=text.split(':',1)[1].strip().split(';',1)[0]
        info(color('✓ '+name,'32')+'  ·  File and checksum verified');return
    if text.startswith('INSTALLATION:'):
        info(color('↓ Installing: '+text.split(':',1)[1].strip(),'36'));return
    if text.startswith('START:'):
        value=text[6:].strip();section('Install app: '+value[4:] if value.startswith('app-') else TITLES.get(value,value));return
    if text.startswith('OK:'):
        value=text[3:].strip();info(color('✓ '+TITLES.get(value,value),'32'));return
    if text.startswith('SKIP:'):
        value=text.split(':',1)[1].strip()
        value=re.sub(r'^([a-z][a-z0-9-]+)',lambda m:TITLES.get(m.group(0),m.group(0)),value)
        info(color('↷ '+value,'90'));return
    if text.startswith(('WARNING:','STOP:','BOOT HELP:')):
        info(color('⚠ '+text,'1;33'));return
    if text.startswith('DOWNLOAD'):
        info(color('↓ '+text,'36'));return
    if text.startswith('MISSING APPS'):
        section('Pending / not installed');info(text.split(':',1)[-1].lstrip());return
    info(text)

def transfer(text):
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    if lines:info(color('↓ '+lines[-1],'36'))

class Progress:
    """Measured transfer progress, or an explicitly indeterminate activity bar."""
    def __init__(self, label, total=None, stream=None, clock=None):
        import time
        self.stream = stream if stream is not None else sys.stdout
        self.clock = clock or time.monotonic
        self.label = label
        self.total = total if isinstance(total, int) and total > 0 else None
        self.started = self.clock()
        self.last = float('-inf')
        self.count = 0
        self.closed = False
        self.visible = False
        self.tty = self.stream.isatty()
        self.width = 0
        self.update(force=True)

    def clear(self):
        if self.tty and self.visible:
            self.stream.write('\r' + ' ' * self.width + '\r')
            self.stream.flush()
            self.visible = False

    def update(self, count=None, force=False):
        if self.closed: return
        if count is not None: self.count = count
        now = self.clock()
        if not force and now-self.last < (0.15 if self.tty else 3): return
        elapsed = max(0, now-self.started)
        if self.total:
            ratio = min(self.count/self.total, 1)
            filled = int(ratio*20)
            bar = '='*filled + ' '*(20-filled)
            status = f'{ratio:6.1%}  {self.count/1048576:.1f}/{self.total/1048576:.1f} MiB'
        else:
            position = int(elapsed*4) % 18
            bar = ' '*position + '===' + ' '*(17-position)
            status = f'{self.count/1048576:.1f} MiB' if self.count else '…'
        if self.count:
            status += f'  {self.count/1048576/max(elapsed,0.001):.1f} MiB/s'
        line = f'  {self.label} [{bar}] {status}  {int(elapsed)}s'
        self.stream.write(('\r' if self.tty else '') + line + (' '*max(0,self.width-len(line)) if self.tty else '\n'))
        self.stream.flush()
        self.width = len(line)
        self.visible = True
        self.last = now

    def close(self):
        if self.closed: return
        self.clear()
        self.closed = True
