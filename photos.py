"""Employee portraits are private, stored alongside roster data in SQLite."""
import base64,binascii,io,warnings
from PIL import Image
from domain import Problem
from db import audit

def decode(encoded):
    if not isinstance(encoded,str):raise Problem('Прикрепите корректную фотографию PNG, JPEG или WebP.')
    if len(encoded)>4*1024*1024*4//3+200:raise Problem('Фотография не должна превышать 4 МБ.',413)
    try:
        header,body=encoded.split(',',1)
        if header not in ('data:image/png;base64','data:image/jpeg;base64','data:image/webp;base64'):raise ValueError()
        content=base64.b64decode(body,validate=True)
        if len(content)>4*1024*1024:raise Problem('Фотография не должна превышать 4 МБ.',413)
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as picture:
                if picture.width*picture.height>20_000_000:raise ValueError()
                mime={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}.get(picture.format)
                if header!='data:'+str(mime)+';base64':raise ValueError()
                picture.verify()
        return content,mime
    except Problem:raise
    except (ValueError,binascii.Error,OSError,SyntaxError,EOFError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise Problem('Прикрепите корректную фотографию PNG, JPEG или WebP.')

def save(conn,user,employee_id,encoded):
    from service import admin
    admin(user)
    if encoded is None:
        conn.execute('DELETE FROM employee_photos WHERE employee_id=?',(employee_id,))
    else:
        content,mime=decode(encoded)
        conn.execute('INSERT INTO employee_photos(employee_id,content,mime) VALUES(?,?,?) ON CONFLICT(employee_id) DO UPDATE SET content=excluded.content,mime=excluded.mime',(employee_id,content,mime))
    audit(conn,user,'Фотография работника','employees',employee_id,None,{'has_photo':encoded is not None})

def get_photo(conn,user,employee_id):
    from service import get
    get(conn,'employees',employee_id)
    if user['role']!='admin' and not conn.execute('SELECT 1 FROM assignments a JOIN project_managers pm ON pm.project_id=a.project_id WHERE a.employee_id=? AND pm.user_id=?',(employee_id,user['id'])).fetchone():raise Problem('Нет доступа к работнику.',403)
    record=conn.execute('SELECT content,mime FROM employee_photos WHERE employee_id=?',(employee_id,)).fetchone()
    if not record:raise Problem('Фотография не найдена.',404)
    return record['content'],record['mime']
