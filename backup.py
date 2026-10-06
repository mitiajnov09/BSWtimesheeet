#!/usr/bin/env python3
"""Consistent SQLite backup, including committed WAL changes."""
import argparse, sqlite3
from pathlib import Path
from app import load_environment
from db import connect
load_environment()
parser=argparse.ArgumentParser(description='Создать согласованную резервную копию SQLite')
parser.add_argument('destination',type=Path)
args=parser.parse_args()
if args.destination.exists():parser.error('Файл уже существует. Выберите новое имя.')
args.destination.parent.mkdir(parents=True,exist_ok=True)
source=connect();target=sqlite3.connect(args.destination)
try:
    source.backup(target)
    result=target.execute('PRAGMA integrity_check').fetchone()[0]
    if result!='ok':raise RuntimeError(result)
finally:target.close();source.close()
args.destination.chmod(0o600)
print('Резервная копия создана: '+str(args.destination))
