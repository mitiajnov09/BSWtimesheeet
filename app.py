#!/usr/bin/env python3
"""Local/production HTTP app. Bind behind HTTPS reverse proxy for deployment."""
import argparse, hashlib, json, logging, os, secrets, sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse
from db import ROOT, connect, migrate, seed, insert, password_hash, audit
from domain import Problem
import service
from pdf_export import export

def load_environment():
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

class Handler(BaseHTTPRequestHandler):
    server_version='Rotations'
    def log_message(self,format,*args):logging.info('%s %s',self.address_string(),format%args)
    def respond(self,status,payload,content_type='application/json; charset=utf-8',cookie=None,filename=None):
        if not isinstance(payload,bytes):payload=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store' if self.path.startswith('/api/') else 'no-cache')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie:self.send_header('Set-Cookie',cookie)
        if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
        self.end_headers();self.wfile.write(payload)
    def read_json(self):
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise Problem('Ожидается JSON.',415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1000000:raise Problem('Неверный размер запроса.',413)
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError()
            return data
        except (ValueError,json.JSONDecodeError):raise Problem('Некорректный запрос.')
    def session_token(self):
        try:
            cookie=SimpleCookie(self.headers.get('Cookie',''));return cookie['rotation_session'].value if 'rotation_session' in cookie else ''
        except Exception:return ''
    def cookie(self,token,clear=False):
        return 'rotation_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age='+('0' if clear else '43200')+('; Secure' if os.getenv('APP_SECURE_COOKIE')=='1' else '')
    def dispatch(self,method):
        conn=None
        try:
            path=urlparse(self.path).path
            if not path.startswith('/api/'):
                if method!='GET':raise Problem('Метод недоступен.',405)
                asset='index.html' if path=='/' else path.lstrip('/')
                target=(ROOT/'static'/asset).resolve()
                if not target.is_relative_to(ROOT/'static') or not target.is_file():raise Problem('Страница не найдена.',404)
                types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml'}
                return self.respond(200,target.read_bytes(),types.get(target.suffix,'application/octet-stream'))
            conn=connect();data=self.read_json() if method in ('POST','DELETE') else {}
            if method!='GET':
                origin=self.headers.get('Origin')
                expected=os.getenv('APP_ORIGIN','http://127.0.0.1:'+os.getenv('APP_PORT','8080'))
                if origin and origin!=expected:raise Problem('Источник запроса не разрешён.',403)
            if path=='/api/login' and method=='POST':
                conn.execute('BEGIN IMMEDIATE')
                result,token=service.login(conn,data,self.client_address[0]);return self.respond(200,result,cookie=self.cookie(token))
            user=service.authenticate(conn,self.session_token())
            if method!='GET' and not secrets.compare_digest(self.headers.get('X-CSRF-Token',''),user['csrf']):raise Problem('Сессия устарела. Обновите страницу.',403)
            if method=='GET' and path=='/api/data':return self.respond(200,service.snapshot(conn,user))
            if method=='GET' and path=='/api/audit':return self.respond(200,service.history(conn,user))
            if method=='POST' and path=='/api/export':return self.respond(200,export(conn,user,data),'application/pdf',filename='rotation-schedule.pdf')
            if method not in ('POST','DELETE'):raise Problem('Маршрут не найден.',404)
            conn.execute('BEGIN IMMEDIATE')
            # Revalidate access inside the write transaction, after acquiring its lock.
            user=service.authenticate(conn,self.session_token())
            if path=='/api/logout':
                conn.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(self.session_token().encode()).hexdigest(),));conn.commit()
                return self.respond(200,{'ok':True},cookie=self.cookie('',True))
            if path=='/api/password':
                if not service.password_matches(data.get('current',''),user['password_hash']):raise Problem('Текущий пароль неверен.',403)
                hashed=password_hash(data.get('password'))
                conn.execute('UPDATE users SET password_hash=?,version=version+1 WHERE id=?',(hashed,user['id']))
                conn.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
                audit(conn,user,'Смена пароля','users',user['id'],None,{'password_changed':True});conn.commit()
                return self.respond(200,{'ok':True},cookie=self.cookie('',True))
            entity=path.removeprefix('/api/')
            if method=='DELETE':result=service.remove(conn,user,entity,data)
            elif entity=='periods':result=service.save_period(conn,user,data)
            elif entity=='cycle':result=service.cycle(conn,user,data)
            elif entity=='events':result=service.save_event(conn,user,data)
            else:result=service.save_admin(conn,user,entity,data)
            conn.commit();return self.respond(200,result)
        except Problem as error:
            if conn:conn.rollback()
            self.respond(error.status,{'error':str(error)})
        except sqlite3.IntegrityError:
            if conn:conn.rollback()
            self.respond(409,{'error':'Такая запись уже существует или связанная запись недоступна.'})
        except Exception:
            if conn:conn.rollback()
            logging.exception('Request failed')
            self.respond(500,{'error':'Не удалось выполнить запрос. Повторите попытку; подробности записаны в журнале сервера.'})
        finally:
            if conn:conn.close()
    def do_GET(self):self.dispatch('GET')
    def do_POST(self):self.dispatch('POST')
    def do_DELETE(self):self.dispatch('DELETE')

if __name__=='__main__':
    load_environment()
    parser=argparse.ArgumentParser(description='Приложение ротаций')
    parser.add_argument('--demo',action='store_true',help='Создать демонстрационную базу и случайные пароли')
    parser.add_argument('--create-admin',metavar='LOGIN',help='Создать первого администратора')
    parser.add_argument('--migrate',action='store_true');args=parser.parse_args()
    conn=connect();migrate(conn)
    if args.demo:
        passwords=seed(conn)
        credentials=ROOT/'data/demo-credentials.txt'
        fd=os.open(credentials,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as f:
            f.write('Локальные демонстрационные учётные записи (случайные пароли):\n')
            for username,password in passwords.items():f.write(username+': '+password+'\n')
        print('Создана демонстрация. Учётные данные: '+str(credentials))
    if args.create_admin:
        import getpass
        if conn.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():parser.error('Администратор уже существует. Используйте интерфейс.')
        password=getpass.getpass('Пароль (минимум 10 символов): ')
        if password!=getpass.getpass('Повторите пароль: '):parser.error('Пароли не совпадают')
        if not __import__('re').fullmatch(r'[a-zA-Z0-9_.-]{3,64}',args.create_admin):parser.error('Недопустимый логин')
        insert(conn,'users',dict(username=args.create_admin,name='Администратор',role='admin',password_hash=password_hash(password)));conn.commit()
        print('Администратор создан.')
    conn.close()
    if args.demo or args.create_admin or args.migrate:raise SystemExit()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    host=os.getenv('APP_HOST','127.0.0.1');port=int(os.getenv('APP_PORT','8080'))
    print(f'Ротации: http://{host}:{port}',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
