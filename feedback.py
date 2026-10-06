"""Private feedback inbox. Screenshots live inside SQLite and its backups."""
import base64, binascii, io, warnings
from PIL import Image
from db import insert, rows
from domain import Problem
from service import admin, project_access, get, check_version, update

MAX_IMAGE=4*1024*1024
FIELDS='f.id,f.user_id,f.project_id,f.kind,f.message,f.status,f.version,f.created_at,u.name user_name,u.username,p.name project_name,(f.screenshot IS NOT NULL) has_screenshot'

def submit(conn,user,data):
    kind=data.get('kind','bug');message=data.get('message')
    if kind not in ('bug','idea'):raise Problem('Выберите ошибку или предложение.')
    if not isinstance(message,str) or not message.strip() or len(message)>5000:raise Problem('Введите сообщение от 1 до 5000 символов.')
    pid=data.get('project_id')
    if pid is not None:project_access(conn,user,pid)
    image=None;mime=None;encoded=data.get('screenshot','')
    if encoded:
        if not isinstance(encoded,str) or len(encoded)>MAX_IMAGE*4//3+200:raise Problem('Скриншот не должен превышать 4 МБ.',413)
        try:
            header,body=encoded.split(',',1)
            if header not in ('data:image/png;base64','data:image/jpeg;base64','data:image/webp;base64'):raise ValueError()
            image=base64.b64decode(body,validate=True)
            if len(image)>MAX_IMAGE:raise Problem('Скриншот не должен превышать 4 МБ.',413)
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(image)) as picture:
                    if picture.width*picture.height>20_000_000:raise ValueError()
                    mime={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}.get(picture.format)
                    if header!='data:'+str(mime)+';base64':raise ValueError()
                    picture.verify()
        except Problem:raise
        except (ValueError,binascii.Error,OSError,SyntaxError,EOFError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise Problem('Прикрепите корректный скриншот PNG, JPEG или WebP.')
    elif encoded is not None and not isinstance(encoded,str):raise Problem('Некорректный скриншот.')
    id=insert(conn,'feedback',dict(user_id=user['id'],project_id=pid,kind=kind,message=message.strip(),screenshot=image,screenshot_type=mime))
    return {'id':id,'ok':True}

def inbox(conn,user):
    admin(user)
    return rows(conn,f'SELECT {FIELDS} FROM feedback f JOIN users u ON u.id=f.user_id LEFT JOIN projects p ON p.id=f.project_id ORDER BY f.id DESC')

def screenshot(conn,user,id):
    admin(user);record=get(conn,'feedback',id)
    if record['screenshot'] is None:raise Problem('Скриншот не найден.',404)
    return record['screenshot'],record['screenshot_type']

def set_status(conn,user,data):
    admin(user);record=get(conn,'feedback',data.get('id'));check_version(record,data)
    status=data.get('status')
    if status not in ('new','reviewed'):raise Problem('Неизвестный статус отзыва.')
    update(conn,'feedback',record,{'status':status})
    return {'ok':True}
