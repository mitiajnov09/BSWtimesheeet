import hashlib, json, os, secrets, sqlite3
from pathlib import Path
from datetime import date, timedelta
from domain import generate_cycle
ROOT=Path(__file__).resolve().parent

def password_hash(password):
    if not isinstance(password, str) or len(password) < 10 or len(password) > 256:
        from domain import Problem
        raise Problem('Пароль должен содержать от 10 до 256 символов.')
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)
    return 'scrypt$'+salt.hex()+'$'+digest.hex()

def password_matches(password, stored):
    try:
        _,salt,digest=stored.split('$')
        computed=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1)
        return secrets.compare_digest(computed.hex(),digest)
    except (ValueError, AttributeError):
        return False

def connect(path=None):
    path=path or os.getenv('APP_DB',str(ROOT/'data/rotations.sqlite3'))
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path,timeout=15)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def migrate(conn):
    for migration in sorted((ROOT/'migrations').glob('*.sql')):
        version=int(migration.name.split('_')[0])
        exists=conn.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()
        if exists and conn.execute('SELECT 1 FROM schema_migrations WHERE version=?',(version,)).fetchone(): continue
        conn.executescript(migration.read_text())
    conn.commit()

def rows(conn,sql,args=()):
    return [dict(r) for r in conn.execute(sql,args).fetchall()]

def insert(conn,table,data):
    fields=list(data)
    cur=conn.execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",[data[f] for f in fields])
    return cur.lastrowid

def audit(conn,user,action,entity,entity_id,before,after,project_id=None):
    insert(conn,'audit',dict(user_id=user['id'],project_id=project_id,action=action,entity=entity,entity_id=entity_id,before_json=json.dumps(before,ensure_ascii=False) if before else None,after_json=json.dumps(after,ensure_ascii=False) if after else None))

def seed(conn):
    if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
        raise RuntimeError('Демонстрация создаётся только в пустой базе.')
    passwords={key:secrets.token_urlsafe(12) for key in ['admin','manager','other']}
    for username,name,role in [('admin','Анна Смирнова','admin'),('manager','Михаил Орлов','manager'),('other','Елена Волкова','manager')]:
        insert(conn,'users',dict(username=username,name=name,role=role,password_hash=password_hash(passwords[username])))
    insert(conn,'sites',dict(name='Stockholm DC-04',country='Швеция',city='Стокгольм',timezone='Europe/Stockholm',address='Kista, Stockholm'))
    insert(conn,'sites',dict(name='Berlin Plant',country='Германия',city='Берлин',timezone='Europe/Berlin',address='Industriepark, Berlin'))
    insert(conn,'projects',dict(name='Data Center — Стокгольм',site_id=1,start='2026-01-01',end='2027-12-31',notes='Монтаж инженерных систем дата-центра.'))
    insert(conn,'projects',dict(name='Производственный комплекс — Берлин',site_id=2,start='2026-01-01',end='2027-12-31',notes='Отдельный проект для проверки прав доступа.'))
    if 'address' in {column['name'] for column in conn.execute('PRAGMA table_info(projects)')}:
        conn.execute("UPDATE projects SET address='Kista, Stockholm',country='SE' WHERE id=1")
        conn.execute("UPDATE projects SET address='Industriepark, Berlin',country='DE' WHERE id=2")
    conn.execute('INSERT INTO project_managers VALUES(1,2)')
    conn.execute('INSERT INTO project_managers VALUES(2,3)')
    names=[('Jonas','Kazlauskas','Электромонтажник'),('Mantas','Petrauskas','Сварщик'),('Tomas','Jankauskas','Монтажник'),('Darius','Stankevičius','Электромонтажник'),('Andrius','Vasiliauskas','Инженер'),('Mindaugas','Žukauskas','Сварщик'),('Paulius','Butkus','Монтажник'),('Lukas','Balčiūnas','Электромонтажник'),('Vytautas','Savickas','Инженер'),('Giedrius','Kavaliauskas','Монтажник')]
    for i,(first,last,specialty) in enumerate(names,1):
        insert(conn,'employees',dict(first_name=first,last_name=last,specialty=specialty,contact=f'demo{i}@example.com',notes='Вымышленный работник для демонстрации.'))
        insert(conn,'assignments',dict(project_id=1,employee_id=i,start='2026-01-01',end='2027-12-31'))
        start=date(2026,9,1)+timedelta(days=i*4)
        for p in generate_cycle(1,i,start.isoformat(),'2027-12-31'):
            if i==3 and p['start']=='2026-09-13':
                p['manual']=1;p['notes']='Рабочая ротация подтверждена индивидуально.'
            if i==5 and p['kind']=='rest' and p['start']<'2026-12-01':
                p['kind']='vacation';p['manual']=1;p['notes']='Согласованный отпуск.'
            if i==7 and p['kind']=='work' and p['start']<'2026-11-01':
                split={**p,'end':'2026-10-11'}
                insert(conn,'periods',split)
                insert(conn,'periods',{**p,'start':'2026-10-12','end':'2026-10-16','kind':'sick','manual':1,'notes':'Больничный: ручное исключение.'})
                p={**p,'start':'2026-10-17'}
            insert(conn,'periods',p)
        insert(conn,'events',dict(project_id=1,employee_id=i,date=f'2026-10-{(i*3)%28+1:02}',time='09:30',timezone='Europe/Stockholm',kind='return' if i%2==0 else 'outbound',route='ARN → VNO' if i%2==0 else 'VNO → ARN',flight=f'SK{1700+i}',notes='Время поездки указано вручную.'))
    insert(conn,'employees',dict(first_name='Rokas',last_name='Jonauskas',specialty='Инженер',contact='demo-berlin@example.com'))
    insert(conn,'assignments',dict(project_id=2,employee_id=11,start='2026-01-01',end='2027-12-31'))
    for p in generate_cycle(2,11,'2026-09-01','2027-12-31'):insert(conn,'periods',p)
    audit(conn,{'id':1},'Создана демонстрация','projects',1,None,{'employees':10},1)
    conn.commit()
    return passwords
