"""Select a UI language; keep one engine and a German string catalog."""
import ast
import importlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
MODULES={'karat','setup_menu','install_apps_and_optimize','terminal_ui','dry_run','downloads','firmware_update'}

class LocalizedLoader(importlib.abc.Loader):
    def __init__(self,name,translations):
        self.name=name;self.translations=translations
    def create_module(self,spec):return None
    def exec_module(self,module):
        path=ROOT/(self.name+'.py')
        tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
        table=self.translations
        class Translate(ast.NodeTransformer):
            def visit_Constant(self,node):
                if isinstance(node.value,str) and node.value in table:
                    node.value=table[node.value]
                return node
        tree=Translate().visit(tree)
        exec(compile(tree,str(path),'exec'),module.__dict__)

class LocalizedFinder(importlib.abc.MetaPathFinder):
    def __init__(self,catalog):self.catalog=catalog
    def find_spec(self,fullname,path=None,target=None):
        if fullname not in MODULES:return None
        loader=LocalizedLoader(fullname,self.catalog.get(fullname,{}))
        return importlib.util.spec_from_file_location(fullname,ROOT/(fullname+'.py'),loader=loader)

def select_language(arguments):
    remaining=[];explicit=None;index=0
    while index<len(arguments):
        arg=arguments[index]
        if arg=='--lang':
            index+=1
            if index>=len(arguments):raise ValueError('--lang requires en or de / --lang benötigt en oder de')
            explicit=arguments[index]
        elif arg.startswith('--lang='):explicit=arg.split('=',1)[1]
        else:remaining.append(arg)
        index+=1
    language=explicit or os.environ.get('FIRE_TV_LANG')
    if language is not None and language not in ('en','de'):
        raise ValueError('Language must be en or de / Sprache muss en oder de sein')
    if not language:
        if sys.stdin.isatty():
            print('\n  Choose language / Sprache wählen\n  [1] English\n  [2] Deutsch\n  EXIT = exit / beenden\n',flush=True)
            while True:
                try:answer=input('  1 / 2 → ').strip().lower()
                except EOFError:return None,remaining
                if answer=='exit':return None,remaining
                if answer in ('1','en','english'):language='en';break
                if answer in ('2','de','deutsch'):language='de';break
                print('  Please choose 1 or 2 / Bitte 1 oder 2 wählen.',flush=True)
        else:language='en'
    return language,remaining

def run(module_name,arguments):
    sys.dont_write_bytecode=True
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    try:language,remaining=select_language(list(arguments))
    except ValueError as error:
        print(str(error),file=sys.stderr);return 2
    if language is None:return 0
    os.environ['FIRE_TV_LANG']=language
    if language=='de':
        import argparse
        labels={
            'usage: ':'Verwendung: ', 'options':'Optionen',
            'positional arguments':'Positionsargumente',
            'optional arguments':'Optionale Argumente',
            'show this help message and exit':'Diese Hilfe anzeigen und beenden',
            'unrecognized arguments: %s':'Unbekannte Argumente: %s',
            'the following arguments are required: %s':'Folgende Argumente sind erforderlich: %s',
            'expected one argument':'Ein Argument wird erwartet',
        }
        argparse._=lambda text:labels.get(text,text)
        catalog=json.loads((ROOT/'locales/de.json').read_text(encoding='utf-8'))
        sys.meta_path.insert(0,LocalizedFinder(catalog))
    sys.argv=[str(ROOT/(module_name+'.py')),*remaining]
    return importlib.import_module(module_name).main()
