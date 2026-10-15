#!/usr/bin/env python3
"""Choose ordered setup phases. Child programs retain all safety checkpoints."""

if __name__ == "__main__":
    import sys
    sys.dont_write_bytecode = True
    from bilingual import run
    sys.exit(run("setup_menu", sys.argv[1:]))

import argparse
import json
from pathlib import Path
import subprocess
import re
import terminal_ui as ui
import sys

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STEPS = {
    '1': ('Temporary root and OTA blocking', 'root', ['--root-phase','temporary']),
    '2': ('Permanent root, one-time backup and Magisk', 'root', ['--root-phase','permanent']),
    'U': ('Update to Fire OS 8.1.8.2 and repair Magisk', 'root', ['--root-phase','update']),
    '3': ('Google Play, microG, Zygisk Next, Vector and FakeGApps', 'root', ['--root-phase','google']),
    '4': ('Set up Emotn Launcher', 'emotn', []),
    '5': ('Install and optimize apps', 'apps', []),
}

ORDER = ['1','2','U','3','4','5']

def selected(value):
    tokens=value.upper().replace(',', ' ').split()
    if not tokens or any(n not in STEPS and n not in ('ALL','ALLE') for n in tokens):
        raise ValueError('Use 1 to 5, U, ALL or ALL U.')
    choices=set(tokens)
    if choices & {'ALL','ALLE'}:
        choices -= {'ALL','ALLE'}
        choices.update(['1','2','3','4','5'])
    return [n for n in ORDER if n in choices]

def runtime_dir(base):
    legacy=base/'.karat-setup'
    current=base/'karat-automation/runtime'
    if legacy.exists() and current.exists():
        raise ValueError('Two runtime folders exist; automatic resume is disabled.')
    return legacy if legacy.exists() else current

def save_plan(path,plan):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)

def resume_choice(base,serial):
    work=runtime_dir(base)
    planpath=work/(serial+'.setup-plan.json')
    saved=json.loads(planpath.read_text(encoding='utf-8')) if planpath.exists() else None
    if saved is not None:
        if not isinstance(saved,dict):
            raise ValueError('Saved setup plan is invalid.')
        if saved.get('serial')!=serial or saved.get('schema')!=1:
            raise ValueError('Saved setup plan does not match the Stick.')
        remaining=saved.get('remaining')
        if not isinstance(remaining,list) or any(n not in STEPS for n in remaining) or remaining!=[n for n in ORDER if n in remaining]:
            raise ValueError('Saved phase sequence is invalid.')
        options=saved.get('options',{})
        if not isinstance(options,dict) or not isinstance(options.get('apps'),(str,type(None))) or any(not isinstance(options.get(key,False),bool) for key in ('adopt_existing','categories')):
            raise ValueError('Saved setup options are invalid.')
        if remaining:
            return remaining,options,True
    path=work/(serial+'.json')
    if path.exists():
        state=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(state,dict):
            raise ValueError('Checkpoint is invalid.')
        if state.get('serial')!=serial or not isinstance(state.get('done'),list):
            raise ValueError('Checkpoint does not match the Stick.')
        if state.get('firmware_update') and 'update-8182-complete' not in state['done']:
            return ['U'],{},False
        pending=state.get('pending')
        done=state['done']
        if pending=='ghostlock':return ['1'],{},False
        if pending in ('unlock','postota','magisk') or ('unlock' in done and ('permanent-cleanup' not in done or 'magisk-setup-boot' not in done)):
            return ['2'],{},False
    return [],{},False

def main():
    parser=argparse.ArgumentParser(description='Run the selected setup phases in order.')
    parser.add_argument('--lang', choices=['en','de'], help='Interface language; selected before setup')
    parser.add_argument('--base',default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument('--serial')
    parser.add_argument('--verbose',action='store_true',help='Show technical details in the terminal')
    parser.add_argument('--steps',help='ALL or a list, e.g. 1,2,3 / 3,4,5')
    parser.add_argument('--dry-run',action='store_true',help='Download/check files; no device required')
    parser.add_argument('--preview-only',action='store_true',help='Simulate the output only')
    parser.add_argument('--dry-run-scenario',choices=['success','boot-timeout'],default='success')
    parser.add_argument('--adopt-existing',action='store_true')
    parser.add_argument('--categories',action='store_true')
    parser.add_argument('--apps',help='App selection for phase 5, e.g. "1 2 6"')
    args=parser.parse_args()
    if args.dry_run and args.preview_only:parser.error('Select only one preview mode.')
    mode='DOWNLOAD TEST · Files are really checked/downloaded; no device required' if args.dry_run else 'PREVIEW · Simulated output only; no downloads' if args.preview_only else 'SETUP · Selected steps run on your Fire TV Stick connected via USB'
    base=Path(args.base).resolve()
    real=not (args.dry_run or args.preview_only)
    if real and not args.serial:
        result=subprocess.run(['adb','-d','get-serialno'],capture_output=True,text=True)
        serial=result.stdout.strip()
        if result.returncode or not re.fullmatch(r'[A-Za-z0-9_-]+',serial) or serial in ('unknown','offline'):
            print('Connect exactly one authorized Fire TV Stick via USB or specify --serial.',flush=True)
            return 2
        args.serial=serial
    if real and not re.fullmatch(r'[A-Za-z0-9_-]+',args.serial or ''):
        parser.error('Invalid USB serial number.')
    resume=[];options={};remembered=False
    if real and not args.steps:
        try:resume,options,remembered=resume_choice(base,args.serial)
        except (ValueError,OSError) as error:
            print('⚠ Cannot resume: '+str(error),flush=True);return 2
        if resume:
            if args.apps is None:args.apps=options.get('apps')
            args.adopt_existing=args.adopt_existing or options.get('adopt_existing',False)
            args.categories=args.categories or options.get('categories',False)
    ui.title('FIRE TV SETUP', mode)
    notes={'U':'Optional · integrated with phase 2 when both are selected','1':'No unlock · Root lasts only until reboot','2':'Unlock → one-time backup → Magisk','3':'Requires Magisk · Google verifier checked before reboot','4':'Requires Vector · Confirm module scope on the TV','5':'A separate numbered app selection follows'}
    ui.menu([(number,label,notes[number]) for number,(label,_,_) in STEPS.items()])
    ui.info('Selection: e.g. 1 2 3 or 3 4 5')
    ui.info('ALL = steps 1–5 · ALL U = steps 1–5 plus update · U = update only · EXIT = exit')
    ui.info('Steps run in order; completed checkpoints are skipped.\n')
    value=args.steps or (' '.join(resume) if resume else None)
    if resume:
        ui.section('AUTOMATIC RESUME')
        ui.info('Saved setup plan: '+', '.join(resume) if remembered else 'Checkpoint detected: resuming phase '+resume[0]+'; earlier steps will not restart.')
        ui.info('Resume uses the same checkpoints and PC backups. Uncertain flash operations remain blocked.')
    if real:ui.info('Fire TV Stick: '+args.serial)
    if not value:
        if (args.dry_run or args.preview_only) and not sys.stdin.isatty():
            value='ALL';ui.info('No interactive input: previewing all steps.')
        else:
            while True:
                try:value=input('  Your selection → ').strip()
                except EOFError:return 2
                if value.upper()=='EXIT':return 0
                try:selected(value);break
                except ValueError as error:print(error)
    try:choices=selected(value)
    except ValueError as error:parser.error(str(error))
    planpath=runtime_dir(base)/(args.serial+'.setup-plan.json') if real else None
    plan={'schema':1,'serial':args.serial,'remaining':choices.copy(),
          'options':{'apps':args.apps,'adopt_existing':args.adopt_existing,'categories':args.categories}}
    if planpath:save_plan(planpath,plan)
    ui.section('Your setup plan')
    for n in choices: ui.info('• '+n+' · '+STEPS[n][0])
    execution=[n for n in choices if not (n=='U' and '2' in choices)]
    for position,n in enumerate(execution,1):
        label,flow,flags=STEPS[n]
        if n=='2' and 'U' in choices: label += ' + Fire OS 8.1.8.2'
        engine=base/'karat-automation'/('install_apps_and_optimize.py' if flow=='apps' else 'karat.py')
        command=[sys.executable,str(engine)]
        if flow!='apps':command.append(flow)
        command+=['--base',str(base),*flags]
        if n=='2' and 'U' in choices:command.append('--update')
        if args.serial:command+=['--serial',args.serial]
        if args.verbose:command.append('--verbose')
        if args.dry_run:command.append('--dry-run')
        if args.preview_only:command.append('--preview-only')
        if flow!='apps' and args.dry_run_scenario!='success':command+=['--dry-run-scenario',args.dry_run_scenario]
        if n=='2' and args.adopt_existing:command.append('--adopt-existing')
        if n=='4':
            if args.categories:command.append('--categories')
        if n=='5' and args.apps is not None:command+=['--apps',args.apps]
        ui.title(f'STEP {position} OF {len(execution)} · PHASE {n}', label)
        try:result=subprocess.run(command)
        except KeyboardInterrupt:return 130
        if result.returncode:
            print('\n⚠ Phase '+n+' was not completed. Later phases will not start; checkpoints are preserved.',flush=True)
            return result.returncode
        if planpath:
            plan['remaining']=[step for step in plan['remaining'] if step!=n and not (n=='2' and step=='U')]
            save_plan(planpath,plan)
    ui.title('SELECTED SETUP COMPLETED', 'Device actions were simulated.' if args.dry_run or args.preview_only else 'All selected phases completed successfully.')
    return 0
if __name__=='__main__':sys.exit(main())
