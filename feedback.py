"""Private, bounded feedback inbox. Screenshots live in SQLite and its backups."""
import time
from db import insert, rows, audit
from domain import Problem
from service import admin, project_access, get, check_version, update
from photos import decode

MAX_IMAGE=4*1024*1024
MAX_USER_IMAGES=20*1024*1024
MAX_TOTAL_IMAGES=200*1024*1024
MAX_USER_PENDING=100
MAX_TOTAL_RECORDS=5000
PAGE_SIZE=50
FIELDS='f.id,f.user_id,f.project_id,f.kind,f.message,f.status,f.version,f.created_at,u.name user_name,u.username,p.name project_name,(f.screenshot IS NOT NULL) has_screenshot'


def submit(conn,user,data):
    # Handler holds BEGIN IMMEDIATE: limits and insert are one atomic operation.
    kind=data.get('kind','bug');message=data.get('message')
    if kind not in ('bug','idea'):raise Problem('Выберите ошибку или предложение.')
    if not isinstance(message,str) or not message.strip() or len(message)>5000:raise Problem('Введите сообщение от 1 до 5000 символов.')
    pid=data.get('project_id')
    if pid is not None:project_access(conn,user,pid)
    now=int(time.time())
    conn.execute('DELETE FROM feedback_rate_events WHERE created_at<=?',(now-3600,))
    if conn.execute('SELECT COUNT(*) FROM feedback_rate_events WHERE user_id=?',(user['id'],)).fetchone()[0]>=5:
        raise Problem('Можно отправить не более 5 отзывов в час. Повторите позже.',429)
    totals=conn.execute('SELECT COUNT(*),COALESCE(SUM(length(screenshot)),0) FROM feedback').fetchone()
    own=conn.execute("SELECT COALESCE(SUM(status='new'),0),COALESCE(SUM(length(screenshot)),0) FROM feedback WHERE user_id=?",(user['id'],)).fetchone()
    if totals[0]>=MAX_TOTAL_RECORDS or own[0]>=MAX_USER_PENDING:
        raise Problem('Лимит отзывов достигнут. Обратитесь к администратору.',429)
    image=None;mime=None;encoded=data.get('screenshot','')
    if encoded:
        image,mime=decode(encoded,label='Скриншот',max_dimension=2560)
    elif encoded is not None and not isinstance(encoded,str):raise Problem('Некорректный скриншот.')
    size=len(image) if image else 0
    if size and (own[1]+size>MAX_USER_IMAGES or totals[1]+size>MAX_TOTAL_IMAGES):
        raise Problem('Лимит хранения скриншотов достигнут. Отправьте отзыв без скриншота или обратитесь к администратору.',413)
    # Deleted IDs remain in audit, preventing stale id/version pairs from matching
    # a different record after SQLite would otherwise reuse the highest rowid.
    id=conn.execute("SELECT MAX(id)+1 FROM (SELECT COALESCE(MAX(id),0) id FROM feedback UNION ALL SELECT COALESCE(MAX(entity_id),0) id FROM audit WHERE entity='feedback')").fetchone()[0]
    insert(conn,'feedback',dict(id=id,user_id=user['id'],project_id=pid,kind=kind,message=message.strip(),screenshot=image,screenshot_type=mime))
    conn.execute('INSERT INTO feedback_rate_events(user_id,created_at) VALUES(?,?)',(user['id'],now))
    return {'id':id,'ok':True}


def inbox(conn,user,page=1,status=''):
    admin(user)
    try:
        if isinstance(page,bool):raise ValueError()
        page=int(page)
        if page<1 or page>100000:raise ValueError()
    except (ValueError,TypeError):raise Problem('Неверная страница отзывов.')
    if status not in ('','new','reviewed'):raise Problem('Неизвестный статус отзыва.')
    where=' WHERE f.status=?' if status else ''
    args=[status] if status else []
    total=conn.execute('SELECT COUNT(*) FROM feedback f'+where,args).fetchone()[0]
    page=min(page,max(1,(total+PAGE_SIZE-1)//PAGE_SIZE))
    items=rows(conn,f'SELECT {FIELDS} FROM feedback f JOIN users u ON u.id=f.user_id LEFT JOIN projects p ON p.id=f.project_id'+where+' ORDER BY f.id DESC LIMIT ? OFFSET ?',args+[PAGE_SIZE,(page-1)*PAGE_SIZE])
    return {'items':items,'total':total,'page':page,'page_size':PAGE_SIZE}


def screenshot(conn,user,id):
    admin(user);record=get(conn,'feedback',id)
    if record['screenshot'] is None:raise Problem('Скриншот не найден.',404)
    return record['screenshot'],record['screenshot_type']


def set_status(conn,user,data):
    admin(user);record=get(conn,'feedback',data.get('id'));check_version(record,data)
    status=data.get('status')
    if status not in ('new','reviewed'):raise Problem('Неизвестный статус отзыва.')
    if status=='new' and record['status']!='new' and conn.execute("SELECT COUNT(*) FROM feedback WHERE user_id=? AND status='new'",(record['user_id'],)).fetchone()[0]>=MAX_USER_PENDING:
        raise Problem('Лимит новых отзывов этого пользователя достигнут.',429)
    update(conn,'feedback',record,{'status':status})
    return {'ok':True}


def remove(conn,user,data):
    admin(user)
    row=conn.execute('SELECT id,user_id,project_id,kind,status,version,created_at,(screenshot IS NOT NULL) has_screenshot FROM feedback WHERE id=?',(data.get('id'),)).fetchone()
    if not row:raise Problem('Запись не найдена.',404)
    record=dict(row);check_version(record,data)
    conn.execute('DELETE FROM feedback WHERE id=?',(record['id'],))
    # Do not copy sensitive message/image payloads into the persistent audit log.
    audit(conn,user,'Удаление отзыва','feedback',record['id'],record,None)
    return {'ok':True}
