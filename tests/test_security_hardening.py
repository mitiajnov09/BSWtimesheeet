import http.client,json,os,socket,tempfile,threading,time,unittest,stat
from pathlib import Path
from unittest.mock import patch
from db import connect,migrate,seed,rows,password_matches
from domain import Problem
import service
from app import Handler,BoundedHTTPServer

class LoginSecurityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'audit.sqlite3');self.conn=connect(self.path);migrate(self.conn);self.passwords=seed(self.conn)
 def tearDown(self):self.conn.close();self.tmp.cleanup()
 def failure(self,username='admin',client='one'):
  with self.assertRaises(Problem) as result:service.login(self.conn,{'username':username,'password':'incorrect'},client)
  return result.exception
 def test_fifth_failure_blocks_login_for_ten_minutes_across_clients_then_repeats(self):
  with patch('service.time.time',return_value=1000):
   for i in range(4):self.assertEqual(self.failure(client=str(i)).status,401)
  with patch('service.time.time',return_value=1010):
   error=self.failure(client='five');self.assertEqual(error.status,429);self.assertEqual(error.retry_after,600)
  with patch('service.time.time',return_value=1609):
   with self.assertRaises(Problem) as result:service.login(self.conn,{'username':'admin','password':self.passwords['admin']},'new')
   self.assertEqual(result.exception.status,429);self.assertEqual(result.exception.retry_after,1)
  with patch('service.time.time',return_value=1610):
   user,token=service.login(self.conn,{'username':'admin','password':self.passwords['admin']},'new');self.assertEqual(user['user']['role'],'admin')
   for i in range(4):self.assertEqual(self.failure(client='repeat'+str(i)).status,401)
   self.assertEqual(self.failure(client='repeat5').retry_after,600)
 def test_success_clears_previous_failures(self):
  for _ in range(4):self.assertEqual(self.failure().status,401)
  service.login(self.conn,{'username':'admin','password':self.passwords['admin']},'one')
  self.assertEqual(self.failure().status,401)
 def test_source_budget_blocks_rotating_usernames_before_hash(self):
  with patch('service.password_matches',return_value=False) as verify:
   for i in range(service.LOGIN_SOURCE_LIMIT):self.assertEqual(self.failure('unknown'+str(i)).status,401)
   self.assertEqual(self.failure('another').status,429)
   self.assertEqual(verify.call_count,service.LOGIN_SOURCE_LIMIT)
 def test_global_budget_blocks_rotating_sources(self):
  with patch('service.password_matches',return_value=False) as verify:
   for i in range(service.LOGIN_GLOBAL_LIMIT):self.assertEqual(self.failure('unknown'+str(i),str(i)).status,401)
   self.assertEqual(self.failure('another','another').status,429)
   self.assertEqual(verify.call_count,service.LOGIN_GLOBAL_LIMIT)
 def test_password_hash_does_not_hold_sqlite_writer_lock(self):
  def verify(password,stored):
   other=connect(self.path)
   try:other.execute('BEGIN IMMEDIATE');other.rollback()
   finally:other.close()
   return password_matches(password,stored)
  with patch('service.password_matches',side_effect=verify):service.login(self.conn,{'username':'admin','password':self.passwords['admin']},'test')
 def test_password_change_during_verification_prevents_old_password_login(self):
  def verify(password,stored):
   other=connect(self.path);other.execute("UPDATE users SET password_hash=? WHERE username='admin'",(service.password_hash('replacementPassword2026'),));other.commit();other.close();return True
  with patch('service.password_matches',side_effect=verify):self.assertEqual(self.failure().status,401)
 def test_database_is_private(self):
  self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode),0o600)

class EmployeeDeletionTests(unittest.TestCase):
 setUp=LoginSecurityTests.setUp
 tearDown=LoginSecurityTests.tearDown
 def test_delete_requires_admin_confirmation_and_versions_and_removes_related_records(self):
  admin=dict(self.conn.execute('SELECT * FROM users WHERE id=1').fetchone());manager=dict(self.conn.execute('SELECT * FROM users WHERE id=2').fetchone());employee=service.get(self.conn,'employees',1)
  payload={'id':1,'version':employee['version'],'schedule_version':employee['schedule_version'],'confirm':'DELETE'}
  with self.assertRaises(Problem) as result:service.remove(self.conn,manager,'employees',payload)
  self.assertEqual(result.exception.status,403)
  with self.assertRaises(Problem):service.remove(self.conn,admin,'employees',{**payload,'confirm':'wrong'})
  with self.assertRaises(Problem) as result:service.remove(self.conn,admin,'employees',{**payload,'schedule_version':-1})
  self.assertEqual(result.exception.status,409)
  remaining=self.conn.execute('SELECT count(*) FROM employees').fetchone()[0]
  self.conn.execute('BEGIN IMMEDIATE');service.remove(self.conn,admin,'employees',payload);self.conn.commit()
  self.assertEqual(self.conn.execute('SELECT count(*) FROM employees').fetchone()[0],remaining-1)
  for table in ['employee_photos','team_members','events','periods','assignments']:
   self.assertEqual(self.conn.execute(f'SELECT count(*) FROM {table} WHERE employee_id=1').fetchone()[0],0)
  self.assertFalse(self.conn.execute('PRAGMA foreign_key_check').fetchall())
  self.assertTrue(self.conn.execute("SELECT 1 FROM audit WHERE action='Окончательное удаление работника'").fetchone())

 def test_deleted_employee_id_is_not_reused(self):
  admin=dict(self.conn.execute('SELECT * FROM users WHERE id=1').fetchone());employee=service.get(self.conn,'employees',self.conn.execute('SELECT max(id) FROM employees').fetchone()[0])
  self.conn.execute('BEGIN IMMEDIATE');service.remove(self.conn,admin,'employees',{'id':employee['id'],'version':employee['version'],'schedule_version':employee['schedule_version'],'confirm':'DELETE'});self.conn.commit()
  replacement=service.save_admin(self.conn,admin,'employees',{'first_name':'New','last_name':'Worker','specialty':'Electrician'})
  self.assertGreater(replacement['id'],employee['id'])

class RequestBoundaryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.previous_db=os.environ.get('APP_DB');os.environ['APP_DB']=str(Path(self.tmp.name)/'http.sqlite3');c=connect();migrate(c);c.close()
  class ShortHandler(Handler):request_timeout=.15
  self.server=BoundedHTTPServer(('127.0.0.1',0),ShortHandler,max_workers=1);self.port=self.server.server_address[1];self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):
  self.server.shutdown();self.server.server_close();self.thread.join()
  if self.previous_db is None:os.environ.pop('APP_DB',None)
  else:os.environ['APP_DB']=self.previous_db
  self.tmp.cleanup()
 def test_http_fifth_failure_returns_retry_after(self):
  def send():
   c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
   c.request('POST','/api/login',json.dumps({'username':'unknown','password':'incorrect'}),{'Content-Type':'application/json'})
   r=c.getresponse();result=(r.status,r.getheader('Retry-After'));r.read();c.close()
   # A one-worker test server must finish the prior handler before the next request.
   self.assertTrue(self.server.request_slots.acquire(timeout=1));self.server.request_slots.release()
   return result
  for _ in range(4):self.assertEqual(send()[0],401)
  status,retry=send();self.assertEqual(status,429);self.assertEqual(retry,'600')

 def test_incomplete_body_times_out(self):
  with socket.create_connection(('127.0.0.1',self.port),timeout=2) as client:
   client.sendall(b'POST /api/login HTTP/1.0\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{')
   response=client.recv(4096);self.assertIn(b'408',response)
 def test_capacity_limit_rejects_second_request_and_recovers(self):
  client=socket.create_connection(('127.0.0.1',self.port),timeout=2);client.sendall(b'GET / HTTP/1.0\r\n')
  time.sleep(.03)
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2);c.request('GET','/api/version');r=c.getresponse();self.assertEqual(r.status,503);self.assertEqual(r.getheader('Retry-After'),'1');r.read();c.close();client.close();time.sleep(.2)
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2);c.request('GET','/api/version');r=c.getresponse();self.assertEqual(r.status,200);r.read();c.close()

if __name__=='__main__':unittest.main()
