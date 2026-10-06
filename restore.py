#!/usr/bin/env python3
"""Restore a checked SQLite backup. Stop the app before replacing its database."""
import argparse, os, sqlite3
from pathlib import Path
from backup import database_path,readonly,check

def restore_backup(source,target,replace=False):
    source=Path(source).resolve();target=Path(target).resolve()
    if not source.is_file():raise ValueError('Копия не найдена.')
    if source==target:raise ValueError('Копия и целевая база должны иметь разные пути.')
    if target.exists() and not replace:raise ValueError('База уже существует. Остановите приложение, сохраните текущую копию и укажите --replace.')
    src=readonly(source)
    try:
        check(src)
        tables={r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'schema_migrations','users','projects','employees','periods'}.issubset(tables):raise ValueError('Это не база BSW ROTACIJA.')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        dst=sqlite3.connect(target,timeout=15)
        try:src.backup(dst);check(dst)
        finally:dst.close()
        target.chmod(0o600)
    finally:src.close()
    return target

def main():
    parser=argparse.ArgumentParser(description='Восстановить SQLite. Приложение должно быть остановлено.')
    parser.add_argument('source',type=Path)
    parser.add_argument('--database',help='Целевая база; по умолчанию APP_DB из окружения/.env')
    parser.add_argument('--replace',action='store_true',help='Разрешить замену существующей базы после остановки приложения')
    args=parser.parse_args()
    try:target=restore_backup(args.source,database_path(args.database),args.replace)
    except (ValueError,OSError,sqlite3.Error) as error:parser.exit(1,str(error)+'\n')
    print('База восстановлена: '+str(target)+'. Выполните app.py --migrate и запустите приложение.')

if __name__=='__main__':main()
