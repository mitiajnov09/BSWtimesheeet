import hashlib, json, re, secrets, time
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from db import ROOT, rows, insert, audit, password_hash, password_matches
from domain import Problem, day, date_range, overlap, validate_periods, generate_cycle, subtract_manual, available_layer

KINDS={'work','rest','vacation','sick'}
EVENT_KINDS={'outbound','return','arrival','departure','note'}
COUNTRIES=json.loads((ROOT/'static/countries.json').read_text())

def required(data,key):
    value=data.get(key)
    if not isinstance(value,str) or not value.strip():raise Problem('Заполните обязательное поле: '+key)
    if len(value)>(180 if key=='name' else 120):raise Problem('Текст слишком длинный в поле: '+key)
    return value.strip()

def timezone(value):
    try:ZoneInfo(value)
    except (ZoneInfoNotFoundError,TypeError,ValueError):raise Problem('Неизвестный часовой пояс. Пример: Europe/Stockholm.')
    return value

def get(conn,table,id):
    r=conn.execute(f'SELECT * FROM {table} WHERE id=?',(id,)).fetchone()
    if not r:raise Problem('Запись не найдена.',404)
    return dict(r)

def admin(user):
    if user['role']!='admin':raise Problem('Доступно только администратору.',403)

def project_access(conn,user,id,edit=False):
    if user['role']!='admin' and not conn.execute('SELECT 1 FROM project_managers WHERE project_id=? AND user_id=?',(id,user['id'])).fetchone():
        raise Problem('Нет доступа к проекту.',403)
    project=get(conn,'projects',id)
    if edit and project['status']=='archived':raise Problem('Проект архивирован. Сначала восстановите его.',409)
    return project

def employee_access(conn,user,project_id,employee_id,edit=False):
    project_access(conn,user,project_id,edit)
    employee=get(conn,'employees',employee_id)
    if not conn.execute('SELECT 1 FROM assignments WHERE project_id=? AND employee_id=?',(project_id,employee_id)).fetchone():
        raise Problem('Работник не назначен на проект.',403)
    if edit and not conn.execute('SELECT 1 FROM assignments WHERE project_id=? AND employee_id=? AND active=1',(project_id,employee_id)).fetchone():raise Problem('Назначение работника на этот проект неактивно.',409)
    if edit and employee['status']=='archived':raise Problem('Работник архивирован. Сначала восстановите его.',409)
    return employee

def check_version(record,data,key='version'):
    if data.get(key)!=record[key]:raise Problem('Запись уже изменена другим пользователем. Обновите данные и повторите правку.',409)

def update(conn,table,record,changes):
    fields=list(changes)
    conn.execute(f"UPDATE {table} SET {','.join(f'{f}=?' for f in fields)},version=version+1 WHERE id=?",[changes[f] for f in fields]+[record['id']])
    return get(conn,table,record['id'])

def employee_periods(conn,id):return rows(conn,'SELECT * FROM periods WHERE employee_id=?',(id,))
def employee_assignments(conn,id):return rows(conn,'SELECT * FROM assignments WHERE employee_id=?',(id,))
def bump(conn,id):conn.execute('UPDATE employees SET schedule_version=schedule_version+1 WHERE id=?',(id,))

def login(conn,data,client_key):
    now=int(time.time())
    username=required(data,'username')
    password=data.get('password','')
    if not isinstance(password,str) or len(password)>256:raise Problem('Неверный логин или пароль.',401)
    key=hashlib.sha256((client_key+'|'+username).encode()).hexdigest()
    limit=conn.execute('SELECT * FROM login_attempts WHERE key=?',(key,)).fetchone()
    if limit and limit['reset_at']>now and limit['attempts']>=10:raise Problem('Слишком много попыток. Повторите через 15 минут.',429)
    user=conn.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
    # Do the same expensive hash operation for nonexistent users.
    stored=user['password_hash'] if user else 'scrypt$'+'00'*16+'$'+'00'*64
    valid=password_matches(password,stored)
    if not valid or not user or not user['active']:
        count=limit['attempts']+1 if limit and limit['reset_at']>now else 1
        conn.execute('INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)',(key,count,now+900 if not limit or limit['reset_at']<=now else limit['reset_at']))
        conn.commit()
        raise Problem('Неверный логин или пароль.',401)
    conn.execute('DELETE FROM login_attempts WHERE key=?',(key,))
    token,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(24)
    conn.execute('DELETE FROM sessions WHERE expires<?',(now,))
    conn.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf,now+43200))
    conn.commit()
    return {'user':public_user(dict(user)),'csrf':csrf},token

def public_user(user):return {k:user[k] for k in ('id','username','name','role','active','version')}

def authenticate(conn,token):
    row=conn.execute('SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>? AND u.active=1',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
    if not row:raise Problem('Войдите в систему.',401)
    return dict(row)

def snapshot(conn,user):
    projects=rows(conn,'SELECT p.*,s.name site_name,s.city FROM projects p JOIN sites s ON s.id=p.site_id '+('' if user['role']=='admin' else 'WHERE p.id IN (SELECT project_id FROM project_managers WHERE user_id=?)'),() if user['role']=='admin' else (user['id'],))
    ids=[p['id'] for p in projects]
    placeholders=','.join('?' for _ in ids) or 'NULL'
    assignments=rows(conn,f'SELECT * FROM assignments WHERE project_id IN ({placeholders})',ids)
    eids=sorted({a['employee_id'] for a in assignments})
    ep=','.join('?' for _ in eids) or 'NULL'
    employees=rows(conn,'SELECT * FROM employees' if user['role']=='admin' else f'SELECT * FROM employees WHERE id IN ({ep})',() if user['role']=='admin' else eids)
    photo_ids={r['employee_id'] for r in rows(conn,'SELECT employee_id FROM employee_photos')}
    for employee in employees:employee['has_photo']=employee['id'] in photo_ids
    managers=rows(conn,f'SELECT pm.*,u.name,u.role FROM project_managers pm JOIN users u ON u.id=pm.user_id WHERE project_id IN ({placeholders})',ids)
    return dict(teams=rows(conn,f'SELECT * FROM teams WHERE project_id IN ({placeholders})',ids),team_members=rows(conn,f'SELECT * FROM team_members WHERE project_id IN ({placeholders})',ids),user=public_user(user),csrf=user['csrf'],projects=projects,employees=employees,assignments=assignments,managers=managers,sites=rows(conn,'SELECT * FROM sites') if user['role']=='admin' else [],users=[public_user(u) for u in rows(conn,'SELECT * FROM users')] if user['role']=='admin' else [],periods=rows(conn,f'SELECT * FROM periods WHERE project_id IN ({placeholders})',ids),events=rows(conn,f'SELECT * FROM events WHERE project_id IN ({placeholders})',ids))

def save_admin(conn,user,entity,data):
    admin(user)
    if entity=='teams':return save_team(conn,user,data)
    if entity=='team-members':return save_team_member(conn,user,data)
    if entity not in ('sites','projects','employees','users','assignments'):raise Problem('Неизвестная сущность.',404)
    old=get(conn,entity,data['id']) if data.get('id') else None
    if old:
        check_version(old,data)
        if entity=='projects':old['manager_ids']=[r['user_id'] for r in rows(conn,'SELECT user_id FROM project_managers WHERE project_id=?',(old['id'],))]
    project_id=None
    if entity=='sites':
        changes={k:required(data,k) for k in ('name','country','city','timezone')}
        changes['timezone']=timezone(changes['timezone']);changes['address']=str(data.get('address',''))[:2000]
    elif entity=='projects':
        site_id=data.get('site_id',old['site_id'] if old else None)
        site=get(conn,'sites',site_id) if site_id else None
        a,b=date_range(data.get('start'),data.get('end'))
        status=data.get('status','active')
        if status not in ('active','archived'):raise Problem('Неизвестный статус.')
        if old:
            assignments=rows(conn,'SELECT * FROM assignments WHERE project_id=?',(old['id'],))
            if any(x['start']<a.isoformat() or x['end']>b.isoformat() for x in assignments):raise Problem('Даты проекта должны охватывать все назначения.',409)
            # A change of site must not create cross-site assignment conflicts.
            for x in assignments:
                others=rows(conn,'SELECT a.*,p.site_id FROM assignments a JOIN projects p ON p.id=a.project_id WHERE a.employee_id=? AND a.project_id!=?',(x['employee_id'],old['id']))
                if site and site['id']!=old['site_id'] and any(z['site_id']!=site['id'] and overlap(x,z) for z in others):raise Problem('Смена объекта создаст конфликт назначений.',409)
        address=data.get('address',(old['address'] if old else '') or (site['address'] or site['city'] if site else ''))
        country=data.get('country',old['country'] if old else site['country'] if site else '')
        if not isinstance(address,str) or not address.strip() or len(address)>2000:raise Problem('Укажите адрес проекта.')
        if 'country' in data:
            if country not in COUNTRIES and not (old and country==old['country']):raise Problem('Выберите страну из списка.')
        elif not country:raise Problem('Выберите страну из списка.')
        changes=dict(name=required(data,'name'),site_id=site['id'] if site else None,address=address.strip(),country=country,start=a.isoformat(),end=b.isoformat(),status=status,notes=str(data.get('notes',''))[:2000])
        manager_ids=data.get('manager_ids',[])
        if not isinstance(manager_ids,list):raise Problem('Выберите руководителей.')
        for id in manager_ids:
            manager=get(conn,'users',id)
            if manager['role'] not in ('manager','secretary') or not manager['active']:raise Problem('Назначайте активных руководителей или секретарей.')
        if not site:
            changes['site_id']=insert(conn,'sites',dict(name=changes['name'],country=country,city='',address=changes['address'],timezone='Europe/Vilnius'))
    elif entity=='employees':
        changes={k:required(data,k) for k in ('first_name','last_name','specialty')}
        changes['leadership']=data.get('leadership',old['leadership'] if old else 'none')
        if changes['leadership'] not in ('none','team_leader','work_manager'):raise Problem('Неизвестная роль работника.')
        changes.update(contact=str(data.get('contact',''))[:500],notes=str(data.get('notes',''))[:2000],status=data.get('status','active'))
        if changes['status'] not in ('active','archived'):raise Problem('Неизвестный статус.')
    elif entity=='users':
        username=required(data,'username')
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{3,64}',username):raise Problem('Логин: 3–64 латинских символа, цифры, точка, дефис или подчёркивание.')
        role=data.get('role',old['role'] if old else 'manager')
        if old and old['role']=='admin' and role!='admin':raise Problem('Роль администратора нельзя изменить.')
        if role not in ('manager','secretary') and not (old and old['role']=='admin' and role=='admin'):
            raise Problem('Выберите роль руководителя или секретаря.')
        changes=dict(username=username,name=required(data,'name'),role=role,active=int(bool(data.get('active',True))))
        if old and old['id']==user['id'] and not changes['active']:raise Problem('Нельзя отключить собственную учётную запись.')
        if not old or data.get('password'):changes['password_hash']=password_hash(data.get('password'))
    else:
        project=get(conn,'projects',data.get('project_id'));employee=get(conn,'employees',data.get('employee_id'))
        if project['status']=='archived' or employee['status']=='archived':raise Problem('Сначала восстановите проект и работника.',409)
        a,b=date_range(data.get('start'),data.get('end'))
        if a.isoformat()<project['start'] or b.isoformat()>project['end']:raise Problem('Назначение выходит за даты проекта.',409)
        changes=dict(project_id=project['id'],employee_id=employee['id'],start=a.isoformat(),end=b.isoformat(),active=int(bool(data.get('active',old['active'] if old else True))))
        others=rows(conn,'SELECT a.*,p.site_id FROM assignments a JOIN projects p ON p.id=a.project_id WHERE a.employee_id=?',(employee['id'],))
        for x in others:
            if old and x['id']==old['id']:continue
            if x['active'] and changes['active'] and overlap(x,changes) and (x['site_id']!=project['site_id'] or x['project_id']==project['id']):raise Problem('Назначение пересекается с существующим назначением на этот проект или другой объект.',409)
        if old and (old['employee_id']!=employee['id'] or old['project_id']!=project['id']):raise Problem('У назначения нельзя менять проект или работника. Создайте новое назначение.')
        validate_periods(employee_periods(conn,employee['id']),[x for x in employee_assignments(conn,employee['id']) if not old or x['id']!=old['id']]+[changes])
        if old:
            affected=rows(conn,'SELECT * FROM events WHERE employee_id=? AND project_id=?',(employee['id'],project['id']))
            assigned=[x for x in employee_assignments(conn,employee['id']) if x['id']!=old['id']]+[changes]
            if any(not any(z['project_id']==ev['project_id'] and z['start']<=ev['date']<=z['end'] for z in assigned) for ev in affected):raise Problem('Даты назначения должны охватывать события работника.',409)
        project_id=project['id']
    id=old['id'] if old else insert(conn,entity,changes)
    new=update(conn,entity,old,changes) if old else get(conn,entity,id)
    if entity=='projects':
        conn.execute('DELETE FROM project_managers WHERE project_id=?',(id,))
        for uid in set(manager_ids):conn.execute('INSERT INTO project_managers VALUES(?,?)',(id,uid))
        project_id=id
        new['manager_ids']=manager_ids
    if entity=='users' and (not new['active'] or data.get('password') or old and old['role']!=new['role']):
        conn.execute('DELETE FROM sessions WHERE user_id=?',(id,))
    if entity=='assignments':bump(conn,changes['employee_id'])
    if entity=='employees' and not old and data.get('assignment'):
        assignment=data['assignment']
        if not isinstance(assignment,dict):raise Problem('Некорректное назначение работника.')
        save_admin(conn,user,'assignments',dict(project_id=assignment.get('project_id'),employee_id=id,start=assignment.get('start'),end=assignment.get('end')))
        if assignment.get('team_id') is not None:
            save_team_member(conn,user,dict(project_id=assignment.get('project_id'),employee_id=id,team_id=assignment['team_id'],version=0))
    if entity=='employees' and 'photo' in data:
        from photos import save
        save(conn,user,id,data['photo'])
    safe_old={k:v for k,v in (old or {}).items() if k!='password_hash'}
    safe_new={k:v for k,v in new.items() if k!='password_hash'}
    audit(conn,user,'Изменение' if old else 'Создание',entity,id,safe_old,safe_new,project_id)
    return safe_new

def save_period(conn,user,data):
    old=get(conn,'periods',data['id']) if data.get('id') else None
    project_id=old['project_id'] if old else data.get('project_id')
    employee_id=old['employee_id'] if old else data.get('employee_id')
    emp=employee_access(conn,user,project_id,employee_id,True)
    check_version(emp,data,'schedule_version')
    if old:check_version(old,data)
    start,end=date_range(data.get('start'),data.get('end'))
    kind=data.get('kind')
    if kind not in KINDS:raise Problem('Неизвестный вид периода.')
    if user['role']=='secretary' and (kind not in ('work','sick') or old and old['kind'] not in ('work','sick') or data.get('scope')=='following'):
        raise Problem('Секретарь может изменять только работу и больничные, по одному периоду.',403)
    changes=dict(project_id=project_id,employee_id=employee_id,start=start.isoformat(),end=end.isoformat(),kind=kind,manual=1,notes=str(data.get('notes',''))[:2000])
    periods=employee_periods(conn,employee_id)
    changes['layer']=old['layer'] if old else available_layer(periods,changes)
    replaced=[old] if old else []
    candidate=[p for p in periods if not old or p['id']!=old['id']]+[changes]
    following=[]
    if old and data.get('scope')=='following':
        shift=start-day(old['start']);duration=end-day(old['end'])
        if shift!=duration:raise Problem('Для сдвига следующих периодов сохраните длительность выбранного периода.')
        following=[p for p in periods if p['project_id']==project_id and p['start']>old['end'] and p.get('layer',0)==old.get('layer',0) and not p['manual']]
        for p in following:
            candidate=[q for q in candidate if q.get('id')!=p['id']]
            candidate.append({**p,'start':(day(p['start'])+shift).isoformat(),'end':(day(p['end'])+shift).isoformat()})
        replaced+=following
    validate_periods(candidate,employee_assignments(conn,employee_id))
    if data.get('preview'):
        return {'changed':replaced,'following':len(following),'proposed':changes,'schedule_version':emp['schedule_version']}
    id=old['id'] if old else insert(conn,'periods',changes)
    new=update(conn,'periods',old,changes) if old else get(conn,'periods',id)
    for p in following:
        q=next(q for q in candidate if q.get('id')==p['id'])
        after=update(conn,'periods',p,{'start':q['start'],'end':q['end']})
        audit(conn,user,'Сдвиг периода','periods',p['id'],p,after,project_id)
    bump(conn,employee_id)
    audit(conn,user,'Изменение периода' if old else 'Создание периода','periods',id,old,new,project_id)
    return new

def cycle(conn,user,data):
    if user['role']=='secretary':raise Problem('Построение циклов доступно администратору и руководителю.',403)
    pid,eid=data.get('project_id'),data.get('employee_id')
    emp=employee_access(conn,user,pid,eid,True);check_version(emp,data,'schedule_version')
    generated=generate_cycle(pid,eid,data.get('start'),data.get('end'),data.get('repeats'),data.get('work_weeks',6),data.get('rest_weeks',2))
    window={'start':generated[0]['start'],'end':generated[-1]['end']}
    all_periods=employee_periods(conn,eid)
    manual=[p for p in all_periods if p['project_id']==pid and p['manual']]
    replaced=[p for p in all_periods if p['project_id']==pid and p.get('layer',0)==0 and not p['manual'] and overlap(p,window)]
    new=subtract_manual(generated,[p for p in manual if p.get('layer',0)==0])
    # Preserve parts of an automatic period that extend beyond the requested window.
    fragments=[]
    for p in replaced:
        for f in subtract_manual([p],[window]):
            fragments.append({k:v for k,v in f.items() if k not in ('id','version')})
    kept=[p for p in all_periods if p not in replaced]
    validate_periods(kept+new+fragments,employee_assignments(conn,eid))
    digest=hashlib.sha256(json.dumps({'replaced':replaced,'new':new,'fragments':fragments,'version':emp['schedule_version']},sort_keys=True).encode()).hexdigest()
    preview=dict(replaced=replaced,created=new,preserved=[p for p in manual if overlap(p,window)],token=digest,schedule_version=emp['schedule_version'])
    if data.get('preview'):return preview
    if data.get('token')!=digest:raise Problem('Сначала просмотрите изменения графика. Предпросмотр устарел.',409)
    for p in replaced:conn.execute('DELETE FROM periods WHERE id=?',(p['id'],))
    for p in new+fragments:insert(conn,'periods',p)
    bump(conn,eid)
    audit(conn,user,'Построение цикла','periods',eid,replaced,new+fragments,pid)
    return {'created':len(new),'preserved':len(preview['preserved'])}

def save_schedule_batch(conn,user,data):
    entity=data.get('entity')
    items=data.get('items')
    if entity not in ('cycle','periods') or not isinstance(items,list) or not items or len(items)>500:
        raise Problem('Выберите работников для планирования.')
    if any(not isinstance(item,dict) or item.get('id') for item in items):
        raise Problem('Групповое планирование доступно только для новых периодов и циклов.')
    ids=[item.get('employee_id') for item in items]
    if any(type(id) is not int for id in ids) or len(set(ids))!=len(ids):
        raise Problem('Список работников содержит повторения или неверные записи.')
    operation=cycle if entity=='cycle' else save_period
    return {'results':[operation(conn,user,item) for item in items]}

def save_event(conn,user,data):
    old=get(conn,'events',data['id']) if data.get('id') else None
    pid=old['project_id'] if old else data.get('project_id');eid=old['employee_id'] if old else data.get('employee_id')
    employee_access(conn,user,pid,eid,True)
    if old:check_version(old,data)
    date=day(data.get('date')).isoformat()
    if not any(a['project_id']==pid and a['start']<=date<=a['end'] for a in employee_assignments(conn,eid)):raise Problem('Событие выходит за даты назначения.',409)
    kind=data.get('kind');event_time=data.get('time','')
    if kind not in EVENT_KINDS:raise Problem('Неизвестное событие.')
    if user['role']=='secretary' and (kind not in ('outbound','return') or old and old['kind'] not in ('outbound','return')):
        raise Problem('Секретарь может изменять только перелёты.',403)
    if event_time and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',event_time):raise Problem('Время указывается в формате ЧЧ:ММ.')
    transport=data.get('transport',old['transport'] if old else 'plane')
    if transport not in ('plane','car','ferry'):raise Problem('Неизвестный вид транспорта.')
    changes=dict(transport=transport,project_id=pid,employee_id=eid,date=date,time=event_time,timezone=timezone(data.get('timezone',old['timezone'] if old else 'Europe/Vilnius')),kind=kind,route=str(data.get('route',''))[:500],flight=str(data.get('flight',''))[:100],notes=str(data.get('notes',''))[:2000])
    id=old['id'] if old else insert(conn,'events',changes)
    new=update(conn,'events',old,changes) if old else get(conn,'events',id)
    audit(conn,user,'Изменение события' if old else 'Создание события','events',id,old,new,pid)
    return new

def remove(conn,user,entity,data):
    if entity=='teams':return remove_team(conn,user,data)
    if entity not in ('periods','events'):raise Problem('Удаление недоступно. Используйте архивирование.',400)
    old=get(conn,entity,data.get('id'))
    emp=employee_access(conn,user,old['project_id'],old['employee_id'],True)
    if user['role']=='secretary' and old['kind'] not in (('work','sick') if entity=='periods' else ('outbound','return')):
        raise Problem('Секретарь может изменять только работу, больничные и перелёты.',403)
    check_version(old,data)
    if entity=='periods':check_version(emp,data,'schedule_version');bump(conn,emp['id'])
    conn.execute(f'DELETE FROM {entity} WHERE id=?',(old['id'],))
    audit(conn,user,'Удаление',entity,old['id'],old,None,old['project_id'])
    return {'ok':True}

def history(conn,user):
    return rows(conn,'SELECT a.*,u.name user_name FROM audit a LEFT JOIN users u ON u.id=a.user_id '+('' if user['role']=='admin' else 'WHERE a.project_id IN (SELECT project_id FROM project_managers WHERE user_id=?)')+' ORDER BY a.id DESC LIMIT 300',() if user['role']=='admin' else (user['id'],))


def save_team_member(conn,user,data):
    admin(user)
    pid,eid=data.get('project_id'),data.get('employee_id')
    employee_access(conn,user,pid,eid)
    team_id=data.get('team_id')
    if team_id is not None:
        team=get(conn,'teams',team_id)
        if team['status']!='active':raise Problem('Команда удалена.',409)
        if team['project_id']!=pid:raise Problem('Команда относится к другому проекту.',403)
    row=conn.execute('SELECT * FROM team_members WHERE project_id=? AND employee_id=?',(pid,eid)).fetchone()
    old=dict(row) if row else None
    if old:check_version(old,data)
    elif data.get('version')!=0:raise Problem('Назначение команды изменилось. Обновите данные.',409)
    changes=dict(project_id=pid,employee_id=eid,team_id=team_id)
    if old:new=update(conn,'team_members',old,changes)
    else:new=get(conn,'team_members',insert(conn,'team_members',changes))
    for tid in {team_id,old['team_id'] if old else None}-{None}:conn.execute('UPDATE teams SET version=version+1 WHERE id=?',(tid,))
    audit(conn,user,'Назначение команды','team_members',new['id'],old,new,pid)
    return new

def save_team(conn,user,data):
    admin(user)
    old=get(conn,'teams',data['id']) if data.get('id') else None
    if old:
        check_version(old,data)
        if old['status']!='active':raise Problem('Команда удалена.',409)
    pid=old['project_id'] if old else data.get('project_id')
    project_access(conn,user,pid,True)
    changes=dict(project_id=pid,name=required(data,'name'))
    members=data.get('members',[])
    if not isinstance(members,list):raise Problem('Выберите работников команды.')
    ids=set()
    for member in members:
        if not isinstance(member,dict) or member.get('employee_id') in ids:raise Problem('Некорректный список работников команды.')
        eid=member.get('employee_id');ids.add(eid)
        employee_access(conn,user,pid,eid)
        existing=conn.execute('SELECT * FROM team_members WHERE project_id=? AND employee_id=?',(pid,eid)).fetchone()
        expected=existing['version'] if existing else 0
        if member.get('version')!=expected:raise Problem('Назначение команды изменилось. Обновите данные.',409)
    new=update(conn,'teams',old,changes) if old else get(conn,'teams',insert(conn,'teams',changes))
    for member in members:
        save_team_member(conn,user,dict(project_id=pid,employee_id=member['employee_id'],team_id=new['id'] if member.get('selected',True) else None,version=member['version']))
    new=get(conn,'teams',new['id'])
    audit(conn,user,'Изменение команды' if old else 'Создание команды','teams',new['id'],old,new,pid)
    return new


def remove_team(conn,user,data):
    admin(user)
    team=get(conn,'teams',data.get('id'));check_version(team,data)
    project_access(conn,user,team['project_id'],True)
    if team['status']!='active':raise Problem('Команда уже удалена.',409)
    mode=data.get('mode')
    if mode not in ('keep_workers','remove_workers'):raise Problem('Выберите способ удаления команды.')
    members=rows(conn,'SELECT * FROM team_members WHERE team_id=?',(team['id'],))
    for member in members:
        updated=update(conn,'team_members',member,{'team_id':None})
        audit(conn,user,'Назначение команды','team_members',member['id'],member,updated,team['project_id'])
        if mode=='remove_workers':
            for assignment in rows(conn,'SELECT * FROM assignments WHERE project_id=? AND employee_id=? AND active=1',(team['project_id'],member['employee_id'])):
                after=update(conn,'assignments',assignment,{'active':0})
                audit(conn,user,'Отключение назначения','assignments',assignment['id'],assignment,after,team['project_id'])
            bump(conn,member['employee_id'])
    updated=update(conn,'teams',team,{'status':'archived'})
    audit(conn,user,'Удаление команды','teams',team['id'],team,{**updated,'mode':mode,'employees':[m['employee_id'] for m in members]},team['project_id'])
    return {'ok':True,'members':len(members)}
