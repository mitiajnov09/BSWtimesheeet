#!/usr/bin/env python3
"""Online SQLite backup; run with no arguments for a dated copy in backups/."""
import argparse, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def database_path(value=None):
    env=ROOT/'.env'
    if env.is_file():
        for line in env.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key,text=line.split('=',1);os.environ.setdefault(key.strip(),text.strip().strip('"').strip("'"))
    return Path(value or os.getenv('APP_DB',str(ROOT/'data/rotations.sqlite3'))).resolve()

def readonly(path):
    return sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=15)

def check(conn):
    if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Проверка целостности SQLite не пройдена.')
    if conn.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Нарушены связи базы данных.')

def create_backup(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if not source.is_file():raise ValueError('База не найдена. Сначала выполните app.py --migrate.')
    if source==destination:raise ValueError('База и копия должны иметь разные пути.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    try:
        with readonly(source) as src,sqlite3.connect(destination) as dst:
            src.backup(dst);check(dst)
    except Exception:
        destination.unlink(missing_ok=True);raise
    finally:
        if 'src' in locals():src.close()
        if 'dst' in locals():dst.close()
    return destination

def main():
    parser=argparse.ArgumentParser(description='Резервная копия BSW ROTACIJA: включает фото и отзывы, можно запускать при работающем приложении.')
    parser.add_argument('destination',nargs='?',type=Path,help='Имя копии; по умолчанию backups/bsw-rotacija-ДАТА.sqlite3')
    parser.add_argument('--database',help='Путь к исходной базе; по умолчанию APP_DB из окружения/.env')
    args=parser.parse_args()
    destination=args.destination or ROOT/'backups'/('bsw-rotacija-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')+'.sqlite3')
    try:result=create_backup(database_path(args.database),destination)
    except (ValueError,OSError,sqlite3.Error) as error:parser.exit(1,str(error)+'\n')
    print('Резервная копия создана: '+str(result))

if __name__=='__main__':main()
