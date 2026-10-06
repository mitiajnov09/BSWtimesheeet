import hashlib, http.client, io, json, os, tempfile, threading, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from datetime import date
from pypdf import PdfReader
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import Handler
from db import connect,migrate,seed,rows,password_matches
from domain import generate_cycle,subtract_manual,validate_periods,Problem
import service
from pdf_export import export

class CalendarTests(unittest.TestCase):
    def test_6_2_across_year(self):
        p=generate_cycle(1,1,'2026-12-15',repeats=2)
        self.assertEqual((p[0]['start'],p[0]['end']),('2026-12-15','2027-01-25'))
        self.assertEqual((p[1]['start'],p[1]['end']),('2027-01-26','2027-02-08'))
        self.assertEqual(p[2]['start'],'2027-02-09')
    def test_leap_year(self):
        p=generate_cycle(1,1,'2024-02-01',repeats=1)
        self.assertEqual(p[0]['end'],'2024-03-13')
        self.assertTrue(p[0]['start']<='2024-02-29'<=p[0]['end'])
        self.assertEqual(date(2024,12,30).isocalendar().week,1)
    def test_end_is_inclusive_and_truncated(self):
        p=generate_cycle(1,1,'2026-10-01','2026-10-07')
        self.assertEqual(len(p),1);self.assertEqual(p[0]['end'],'2026-10-07')
    def test_exceptions_split_without_loss(self):
        base=generate_cycle(1,1,'2026-10-01','2026-11-25')
        exception={'start':'2026-10-10','end':'2026-10-15'}
        new=subtract_manual(base,[exception]);self.assertEqual(new[0]['end'],'2026-10-09');self.assertEqual(new[1]['start'],'2026-10-16')
        self.assertFalse(any(p['start']<=exception['start']<=p['end'] for p in new))
    def test_invalid_inputs(self):
        for kwargs in [dict(work_weeks=0),dict(rest_weeks=-1),dict(work_weeks='oops'),dict(repeats=101)]:
            with self.assertRaises(Problem):generate_cycle(1,1,'2026-10-01','2026-12-31',**kwargs)

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.conn=connect(str(Path(self.tmp.name)/'db.sqlite'));migrate(self.conn);self.passwords=seed(self.conn)
        self.admin=dict(self.conn.execute('SELECT * FROM users WHERE id=1').fetchone());self.manager=dict(self.conn.execute('SELECT * FROM users WHERE id=2').fetchone())
    def tearDown(self):self.conn.close();self.tmp.cleanup()
    def test_passwords_are_salted_hashes(self):
        self.assertTrue(self.admin['password_hash'].startswith('scrypt$'));self.assertNotIn(self.passwords['admin'],self.admin['password_hash']);self.assertTrue(password_matches(self.passwords['admin'],self.admin['password_hash']))
    def test_manager_snapshot_and_export_isolation(self):
        self.manager['csrf']='test';data=service.snapshot(self.conn,self.manager)
        self.assertEqual([p['id'] for p in data['projects']],[1]);self.assertEqual(len(data['employees']),10);self.assertEqual(data['users'],[])
        self.assertTrue(all(p['project_id']==1 for p in data['periods']));self.assertTrue(all(a['project_id']==1 for a in service.history(self.conn,self.manager)))
        with self.assertRaises(Problem) as ctx:export(self.conn,self.manager,{'project_id':2,'start':'2026-01-01','end':'2026-12-31'})
        self.assertEqual(ctx.exception.status,403)
        with self.assertRaises(Problem):export(self.conn,self.manager,{'project_id':1,'start':'2026-01-01','end':'2026-12-31','employee_ids':[11]})
    def test_admin_operations_denied_to_manager(self):
        with self.assertRaises(Problem) as ctx:service.save_admin(self.conn,self.manager,'employees',{})
        self.assertEqual(ctx.exception.status,403)
    def test_cross_object_assignment_conflict(self):
        with self.assertRaises(Problem) as ctx:service.save_admin(self.conn,self.admin,'assignments',{'project_id':2,'employee_id':1,'start':'2026-10-01','end':'2026-11-01'})
        self.assertEqual(ctx.exception.status,409)
    def test_period_layers_and_assignment_boundaries(self):
        before=service.employee_periods(self.conn,1)
        payload=dict(employee_id=1,project_id=1,schedule_version=1,kind='sick',start='2026-10-01',end='2026-10-03')
        added=service.save_period(self.conn,self.manager,payload)
        self.assertEqual(added['layer'],1)
        self.assertEqual(before,[p for p in service.employee_periods(self.conn,1) if p['id']!=added['id']])
        second=service.save_period(self.conn,self.manager,{**payload,'schedule_version':2,'kind':'vacation'})
        self.assertEqual(second['layer'],2)
        validate_periods(service.employee_periods(self.conn,1),service.employee_assignments(self.conn,1))
        with self.assertRaises(Problem):service.save_period(self.conn,self.manager,{**payload,'schedule_version':3,'start':'2028-01-01','end':'2028-01-03'})
    def test_overlays_survive_cycle_and_same_lane_conflicts(self):
        added=service.save_period(self.conn,self.manager,dict(employee_id=1,project_id=1,schedule_version=1,kind='sick',start='2026-10-01',end='2026-10-03'))
        payload=dict(employee_id=1,project_id=1,schedule_version=2,start='2026-10-01',end='2026-12-31')
        preview=service.cycle(self.conn,self.manager,{**payload,'preview':True})
        service.cycle(self.conn,self.manager,{**payload,'token':preview['token']})
        self.assertEqual(added,service.get(self.conn,'periods',added['id']))
        periods=service.employee_periods(self.conn,1)
        with self.assertRaises(Problem):validate_periods(periods+[{**added,'id':999}],service.employee_assignments(self.conn,1))
    def test_deactivate_restore_preserves_all_data(self):
        employee=service.get(self.conn,'employees',1)
        periods=service.employee_periods(self.conn,1);assignments=service.employee_assignments(self.conn,1)
        archived=service.save_admin(self.conn,self.admin,'employees',{**employee,'status':'archived'})
        self.assertEqual(service.get(self.conn,'employees',1)['status'],'archived')
        service.save_admin(self.conn,self.admin,'employees',{**archived,'status':'active'})
        self.assertEqual(periods,service.employee_periods(self.conn,1));self.assertEqual(assignments,service.employee_assignments(self.conn,1))
    def test_localized_layered_pdf(self):
        service.save_period(self.conn,self.manager,dict(employee_id=1,project_id=1,schedule_version=1,kind='sick',start='2026-10-01',end='2026-10-03'))
        for language,label,sick in [('lt','Spalis','Nedarbingumas'),('pl','Październik','Zwolnienie lekarskie')]:
            pdf=export(self.conn,self.manager,dict(project_id=1,start='2026-10-01',end='2026-10-31',language=language,employee_ids=[1],include_notes=False,include_events=False))
            text=''.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
            self.assertIn(label,text);self.assertIn(sick,text)
    def test_optimistic_concurrency_and_audit(self):
        p=rows(self.conn,'SELECT * FROM periods WHERE employee_id=1 ORDER BY start')[0]
        payload={**p,'schedule_version':1,'notes':'Правка руководителя'}
        self.conn.execute('BEGIN IMMEDIATE');service.save_period(self.conn,self.manager,payload);self.conn.commit()
        with self.assertRaises(Problem) as ctx:service.save_period(self.conn,self.manager,payload)
        self.assertEqual(ctx.exception.status,409)
        a=rows(self.conn,"SELECT * FROM audit WHERE action='Изменение периода'")[0]
        self.assertEqual(a['user_id'],2);self.assertIn('Правка руководителя',a['after_json'])
    def test_cycle_requires_preview_and_preserves_exceptions(self):
        manual=rows(self.conn,'SELECT * FROM periods WHERE employee_id=7 AND manual=1')
        payload=dict(employee_id=7,project_id=1,schedule_version=1,start='2026-10-01',end='2027-02-28',work_weeks=6,rest_weeks=2)
        before=rows(self.conn,'SELECT * FROM periods WHERE employee_id=7')
        preview=service.cycle(self.conn,self.manager,{**payload,'preview':True})
        self.assertEqual(before,rows(self.conn,'SELECT * FROM periods WHERE employee_id=7'))
        with self.assertRaises(Problem):service.cycle(self.conn,self.manager,payload)
        self.conn.execute('BEGIN IMMEDIATE');service.cycle(self.conn,self.manager,{**payload,'token':preview['token']});self.conn.commit()
        self.assertEqual(manual,rows(self.conn,'SELECT * FROM periods WHERE employee_id=7 AND manual=1'))
        validate_periods(service.employee_periods(self.conn,7),service.employee_assignments(self.conn,7))
        self.assertTrue(any(p['start']<'2026-10-01' for p in service.employee_periods(self.conn,7)))
        with self.assertRaises(Problem):service.cycle(self.conn,self.manager,{**payload,'token':preview['token']})
    def test_following_shift_preserves_manual_and_validates_conflicts(self):
        p=rows(self.conn,'SELECT * FROM periods WHERE employee_id=1 ORDER BY start')[0]
        # Negative shift moves the entire automatic sequence earlier, still within assignment.
        from domain import day
        from datetime import timedelta
        payload={**p,'schedule_version':1,'scope':'following','start':(day(p['start'])-timedelta(days=1)).isoformat(),'end':(day(p['end'])-timedelta(days=1)).isoformat()}
        preview=service.save_period(self.conn,self.manager,{**payload,'preview':True})
        self.assertGreater(preview['following'],1)
        service.save_period(self.conn,self.manager,payload)
        validate_periods(service.employee_periods(self.conn,1),service.employee_assignments(self.conn,1))
    def test_archive_preserves_history(self):
        e=service.get(self.conn,'employees',1);before=service.employee_periods(self.conn,1)
        service.save_admin(self.conn,self.admin,'employees',{**e,'status':'archived'})
        self.assertEqual(before,service.employee_periods(self.conn,1))
        with self.assertRaises(Problem):service.save_period(self.conn,self.manager,{'employee_id':1,'project_id':1,'schedule_version':1,'kind':'work','start':'2026-01-01','end':'2026-01-02'})
    def test_event_overlays_work_period_and_has_timezone(self):
        p=rows(self.conn,'SELECT * FROM periods WHERE employee_id=1 ORDER BY start')[0]
        before=service.employee_periods(self.conn,1)
        ev=service.save_event(self.conn,self.manager,dict(employee_id=1,project_id=1,date=p['start'],kind='outbound',time='14:20',timezone='Europe/Stockholm',route='VNO → ARN',flight='SK123'))
        self.assertEqual(ev['timezone'],'Europe/Stockholm');self.assertEqual(before,service.employee_periods(self.conn,1))
        with self.assertRaises(Problem):service.save_event(self.conn,self.manager,{**ev,'timezone':'Wrong/Zone'})
    def test_pdf_full_year_is_paginated_with_cyrillic(self):
        pdf=export(self.conn,self.manager,dict(project_id=1,start='2026-01-01',end='2026-12-31',paper='A4',include_events=True,include_notes=True))
        reader=PdfReader(io.BytesIO(pdf));self.assertGreaterEqual(len(reader.pages),14)
        text='\n'.join(p.extract_text() for p in reader.pages)
        self.assertIn('Декабрь 2026',text);self.assertIn('31',text);self.assertIn('Kazlauskas Jonas',text);self.assertIn('Europe/Stockholm',text)
        for page in reader.pages[:14]:
            text=page.extract_text();self.assertIn('Работник / специальность',text);self.assertIn('Работа',text);self.assertGreater(float(page.mediabox.width),float(page.mediabox.height))
    def test_multiple_managers_and_projects(self):
        self.conn.execute('INSERT INTO project_managers VALUES(1,3)')
        other=dict(self.conn.execute('SELECT * FROM users WHERE id=3').fetchone());other['csrf']='test'
        data=service.snapshot(self.conn,other)
        self.assertEqual({p['id'] for p in data['projects']},{1,2})
        self.assertEqual(len(data['employees']),11)
        self.assertEqual(len([m for m in data['managers'] if m['project_id']==1]),2)
    def test_foreign_period_mutation_denied(self):
        p=rows(self.conn,'SELECT * FROM periods WHERE project_id=2')[0]
        with self.assertRaises(Problem) as ctx:service.save_period(self.conn,self.manager,{**p,'schedule_version':1})
        self.assertEqual(ctx.exception.status,403)
    def test_pdf_long_names_and_worker_pagination(self):
        long_last='Оченьдлиннаяфамилия'*5
        self.conn.execute('UPDATE employees SET last_name=? WHERE id=1',(long_last,))
        # A long team must paginate by both dates and employee rows.
        for i in range(12,37):
            self.conn.execute('INSERT INTO employees(id,first_name,last_name,specialty) VALUES(?,?,?,?)',(i,'Иван','Работник '+str(i),'Монтажник'))
            self.conn.execute('INSERT INTO assignments(project_id,employee_id,start,end) VALUES(1,?,?,?)',(i,'2026-01-01','2027-12-31'))
        pdf=export(self.conn,self.manager,dict(project_id=1,start='2026-10-01',end='2026-11-01',paper='A3',include_notes=False,include_events=False))
        reader=PdfReader(io.BytesIO(pdf));self.assertGreater(len(reader.pages),1)
        text=''.join(p.extract_text().replace('\n','') for p in reader.pages)
        self.assertIn(long_last,text);self.assertIn('Работник 36',text)
    def test_travel_transport_defaults_updates_and_preserves_schedule(self):
        event=service.get(self.conn,'events',1)
        self.assertEqual(event['transport'],'plane')
        before=service.employee_periods(self.conn,1)
        car=service.save_event(self.conn,self.manager,{**event,'transport':'car'})
        self.assertEqual(service.get(self.conn,'events',1)['transport'],'car')
        with self.assertRaises(Problem) as ctx:service.save_event(self.conn,self.manager,{**event,'transport':'ferry'})
        self.assertEqual(ctx.exception.status,409)
        ferry=service.save_event(self.conn,self.manager,{**car,'transport':'ferry'})
        with self.assertRaises(Problem):service.save_event(self.conn,self.manager,{**ferry,'transport':'train'})
        self.assertEqual(before,service.employee_periods(self.conn,1))
        service.remove(self.conn,self.manager,'events',{'id':ferry['id'],'version':ferry['version']})
        self.assertEqual(before,service.employee_periods(self.conn,1))
    def test_travel_transport_pdf_and_project_access(self):
        event=service.get(self.conn,'events',1)
        service.save_event(self.conn,self.manager,{**event,'transport':'ferry'})
        pdf=export(self.conn,self.manager,dict(project_id=1,start='2026-10-01',end='2026-10-31',employee_ids=[1],language='lt'))
        text=''.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
        self.assertIn('Keltas',text)
        other=service.get(self.conn,'users',3)
        with self.assertRaises(Problem) as ctx:service.save_event(self.conn,other,{**event,'transport':'car'})
        self.assertEqual(ctx.exception.status,403)
    def test_migrations_are_idempotent(self):
        migrate(self.conn);migrate(self.conn);self.assertEqual(self.conn.execute('SELECT count(*) FROM schema_migrations').fetchone()[0],7)

class EmployeePhotoTests(unittest.TestCase):
    setUp=DatabaseTests.setUp
    tearDown=DatabaseTests.tearDown
    image=lambda self: FeedbackTests.image(self)
    def test_photo_upload_replacement_removal_and_private_snapshot(self):
        import photos
        image,raw=self.image();old=service.get(self.conn,'employees',1)
        updated=service.save_admin(self.conn,self.admin,'employees',{**old,'photo':image})
        self.assertEqual(photos.get_photo(self.conn,self.manager,1),(raw,'image/png'))
        self.manager['csrf']='test';snapshot=service.snapshot(self.conn,self.manager)
        employee=next(e for e in snapshot['employees'] if e['id']==1)
        self.assertTrue(employee['has_photo']);self.assertNotIn('photo',employee)
        with self.assertRaises(Problem) as ctx:photos.get_photo(self.conn,service.get(self.conn,'users',3),1)
        self.assertEqual(ctx.exception.status,403)
        with self.assertRaises(Problem):service.save_admin(self.conn,self.manager,'employees',{**updated,'photo':None})
        with self.assertRaises(Problem) as ctx:service.save_admin(self.conn,self.admin,'employees',{**old,'photo':None})
        self.assertEqual(ctx.exception.status,409)
        service.save_admin(self.conn,self.admin,'employees',{**updated,'photo':None})
        with self.assertRaises(Problem) as ctx:photos.get_photo(self.conn,self.manager,1)
        self.assertEqual(ctx.exception.status,404)
    def test_pdf_photo_option_includes_and_excludes_images(self):
        image,_=self.image();old=service.get(self.conn,'employees',1);service.save_admin(self.conn,self.admin,'employees',{**old,'photo':image})
        for enabled in [True,False]:
            pdf=export(self.conn,self.manager,dict(project_id=1,start='2026-10-01',end='2026-10-14',employee_ids=[1,2],include_photos=enabled,include_notes=False))
            reader=PdfReader(io.BytesIO(pdf));count=sum(len(page.images) for page in reader.pages)
            self.assertEqual(count,1 if enabled else 0)
            self.assertIn('Kazlauskas Jonas',''.join(page.extract_text().replace('\n',' ') for page in reader.pages))
    def test_invalid_photo_rejected(self):
        import photos
        for value in ['data:image/svg+xml;base64,PHN2Zy8+','data:image/png;base64,ZmFrZQ==',{},'x'*(4*1024*1024*4//3+201)]:
            with self.assertRaises(Problem):photos.decode(value)

class FeedbackTests(unittest.TestCase):
    setUp=DatabaseTests.setUp
    tearDown=DatabaseTests.tearDown
    def image(self):
        import base64
        from PIL import Image
        buffer=io.BytesIO();Image.new('RGB',(12,12),'red').save(buffer,format='PNG')
        return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode(),buffer.getvalue()
    def test_submit_is_private_and_author_is_session_user(self):
        import feedback
        image,raw=self.image()
        result=feedback.submit(self.conn,self.manager,dict(kind='bug',message='Ошибка графика',screenshot=image,project_id=1,user_id=1))
        self.conn.commit()
        records=feedback.inbox(self.conn,self.admin)
        self.assertEqual(records[0]['user_id'],self.manager['id']);self.assertEqual(records[0]['has_screenshot'],1)
        self.assertNotIn('screenshot',records[0])
        self.assertEqual(feedback.screenshot(self.conn,self.admin,result['id']),(raw,'image/png'))
        for user in [self.manager,{**self.manager,'role':'secretary'}]:
            with self.assertRaises(Problem) as ctx:feedback.inbox(self.conn,user)
            self.assertEqual(ctx.exception.status,403)
            with self.assertRaises(Problem) as ctx:feedback.screenshot(self.conn,user,result['id'])
            self.assertEqual(ctx.exception.status,403)
    def test_status_changes_admin_only_with_versions(self):
        import feedback
        result=feedback.submit(self.conn,{**self.manager,'role':'secretary'},dict(kind='idea',message='Улучшение'))
        payload=dict(id=result['id'],version=1,status='reviewed')
        with self.assertRaises(Problem):feedback.set_status(self.conn,self.manager,payload)
        feedback.set_status(self.conn,self.admin,payload)
        self.assertEqual(feedback.inbox(self.conn,self.admin)[0]['status'],'reviewed')
        with self.assertRaises(Problem) as ctx:feedback.set_status(self.conn,self.admin,payload)
        self.assertEqual(ctx.exception.status,409)
    def test_invalid_feedback_rejected_without_insert(self):
        import feedback
        image,_=self.image()
        for fields in [dict(message=''),dict(message='a'*5001),dict(message='ok',kind='unknown'),dict(message='ok',screenshot='data:image/svg+xml;base64,PHN2Zy8+'),dict(message='ok',screenshot='data:image/png;base64,ZmFrZQ=='),dict(message='ok',screenshot=image.replace('image/png','image/jpeg')),dict(message='ok',screenshot='x'*(feedback.MAX_IMAGE*4//3+201))]:
            with self.assertRaises(Problem):feedback.submit(self.conn,self.manager,fields)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM feedback').fetchone()[0],0)
        with self.assertRaises(Problem):feedback.submit(self.conn,self.manager,dict(message='ok',project_id=2))
    def test_feedback_screenshots_survive_sqlite_backup(self):
        import feedback,sqlite3
        image,raw=self.image();result=feedback.submit(self.conn,self.admin,dict(kind='idea',message='Хранить отзыв',screenshot=image));self.conn.commit()
        target=sqlite3.connect(':memory:');self.conn.backup(target)
        self.assertEqual(target.execute('SELECT screenshot FROM feedback WHERE id=?',(result['id'],)).fetchone()[0],raw);target.close()

class SecretaryAndTeamTests(unittest.TestCase):
    setUp=DatabaseTests.setUp
    tearDown=DatabaseTests.tearDown
    def secretary(self):
        user=service.save_admin(self.conn,self.admin,'users',dict(username='secretary',name='Тестовый секретарь',password='Test-secretary-password',role='secretary',active=True))
        self.conn.execute('INSERT INTO project_managers VALUES(1,?)',(user['id'],))
        return {**user,'csrf':'test'}
    def test_secretary_scope_and_allowed_edits(self):
        user=self.secretary();snapshot=service.snapshot(self.conn,user)
        self.assertEqual([p['id'] for p in snapshot['projects']],[1]);self.assertEqual(len(snapshot['employees']),10)
        self.assertEqual(snapshot['users'],[])
        period=service.save_period(self.conn,user,dict(project_id=1,employee_id=1,start='2026-10-01',end='2026-10-02',kind='sick',schedule_version=1))
        edited=service.save_period(self.conn,user,{**period,'schedule_version':2,'kind':'work'})
        self.assertEqual(edited['kind'],'work')
        event=service.save_event(self.conn,user,dict(project_id=1,employee_id=1,date='2026-10-01',kind='outbound',timezone='Europe/Stockholm'))
        self.assertEqual(service.save_event(self.conn,user,{**event,'kind':'return'})['kind'],'return')
        with self.assertRaises(Problem):service.project_access(self.conn,user,2)
    def test_secretary_cannot_manage_users_workers_teams_or_other_statuses(self):
        user=self.secretary()
        for entity in ['users','employees','projects','assignments','teams','team-members']:
            with self.assertRaises(Problem) as error:service.save_admin(self.conn,user,entity,{})
            self.assertEqual(error.exception.status,403)
        for kind in ['rest','vacation']:
            with self.assertRaises(Problem) as error:service.save_period(self.conn,user,dict(project_id=1,employee_id=1,start='2026-10-01',end='2026-10-02',kind=kind,schedule_version=1))
            self.assertEqual(error.exception.status,403)
        rest=next(p for p in service.employee_periods(self.conn,1) if p['kind']=='rest')
        with self.assertRaises(Problem):service.save_period(self.conn,user,{**rest,'kind':'work','schedule_version':1})
        with self.assertRaises(Problem):service.remove(self.conn,user,'periods',{**rest,'schedule_version':1})
        with self.assertRaises(Problem):service.cycle(self.conn,user,{})
        with self.assertRaises(Problem):service.save_event(self.conn,user,dict(project_id=1,employee_id=1,date='2026-10-01',kind='note',timezone='Europe/Stockholm'))
    def test_teams_project_isolation_and_membership_versions(self):
        team=service.save_admin(self.conn,self.admin,'teams',dict(project_id=1,name='Электрики',members=[dict(employee_id=1,version=0),dict(employee_id=4,version=0)]))
        other=service.save_admin(self.conn,self.admin,'teams',dict(project_id=2,name='Электрики'))
        self.manager['csrf']='test';data=service.snapshot(self.conn,self.manager)
        self.assertEqual([t['id'] for t in data['teams']],[team['id']]);self.assertEqual(len(data['team_members']),2)
        with self.assertRaises(Problem):service.save_team_member(self.conn,self.admin,dict(project_id=1,employee_id=1,team_id=other['id'],version=1))
        removed=service.save_team_member(self.conn,self.admin,dict(project_id=1,employee_id=1,team_id=None,version=1))
        self.assertIsNone(removed['team_id'])
        with self.assertRaises(Problem):service.save_team_member(self.conn,self.admin,dict(project_id=1,employee_id=1,team_id=team['id'],version=1))
    def test_worker_card_with_assignment_and_team(self):
        team=service.save_team(self.conn,self.admin,dict(project_id=1,name='Монтажники'))
        users_before=rows(self.conn,'SELECT * FROM users')
        employee=service.save_admin(self.conn,self.admin,'employees',dict(first_name='Тест',last_name='Работник',specialty='Монтажник',assignment=dict(project_id=1,start='2026-10-01',end='2027-01-01',team_id=team['id'])))
        self.assertEqual(users_before,rows(self.conn,'SELECT * FROM users'))
        self.assertEqual(service.employee_assignments(self.conn,employee['id'])[0]['project_id'],1)
        self.assertEqual(self.conn.execute('SELECT team_id FROM team_members WHERE employee_id=?',(employee['id'],)).fetchone()[0],team['id'])
        self.assertFalse(self.conn.execute('PRAGMA foreign_key_check').fetchall())
    def test_admin_role_cannot_be_lost_or_granted(self):
        with self.assertRaises(Problem):service.save_admin(self.conn,self.admin,'users',{**self.admin,'role':'secretary'})
        with self.assertRaises(Problem):service.save_admin(self.conn,self.admin,'users',dict(username='new-admin',name='Новый',role='admin',password='Test-password-only'))
    def test_delete_team_keep_workers(self):
        team=service.save_team(self.conn,self.admin,dict(project_id=1,name='Команда',members=[dict(employee_id=1,version=0)]))
        before=service.employee_periods(self.conn,1)
        service.remove(self.conn,self.admin,'teams',dict(id=team['id'],version=team['version'],mode='keep_workers'))
        self.assertEqual(service.get(self.conn,'teams',team['id'])['status'],'archived')
        self.assertEqual(service.employee_assignments(self.conn,1)[0]['active'],1)
        self.assertIsNone(rows(self.conn,'SELECT * FROM team_members WHERE employee_id=1')[0]['team_id'])
        self.assertEqual(before,service.employee_periods(self.conn,1))
    def test_delete_team_remove_workers_is_project_scoped(self):
        team=service.save_team(self.conn,self.admin,dict(project_id=1,name='Команда',members=[dict(employee_id=1,version=0)]))
        before=service.employee_periods(self.conn,1)
        service.remove(self.conn,self.admin,'teams',dict(id=team['id'],version=team['version'],mode='remove_workers'))
        self.assertEqual(service.employee_assignments(self.conn,1)[0]['active'],0)
        self.assertEqual(service.get(self.conn,'employees',1)['status'],'active')
        self.assertEqual(before,service.employee_periods(self.conn,1))
        self.assertEqual(service.employee_assignments(self.conn,11)[0]['active'],1)
        with self.assertRaises(Problem):service.employee_access(self.conn,self.manager,1,1,True)
    def test_team_delete_stale_membership_and_access(self):
        team=service.save_team(self.conn,self.admin,dict(project_id=1,name='Команда'))
        service.save_team_member(self.conn,self.admin,dict(project_id=1,employee_id=1,team_id=team['id'],version=0))
        with self.assertRaises(Problem):service.remove(self.conn,self.admin,'teams',dict(id=team['id'],version=team['version'],mode='keep_workers'))
        current=service.get(self.conn,'teams',team['id'])
        with self.assertRaises(Problem) as ctx:service.remove(self.conn,self.secretary(),'teams',dict(id=team['id'],version=current['version'],mode='keep_workers'))
        self.assertEqual(ctx.exception.status,403)
    def test_leadership_badges_do_not_create_accounts(self):
        employee=service.get(self.conn,'employees',1);users=rows(self.conn,'SELECT * FROM users')
        updated=service.save_admin(self.conn,self.admin,'employees',{**employee,'leadership':'team_leader'})
        self.assertEqual(updated['leadership'],'team_leader')
        updated=service.save_admin(self.conn,self.admin,'employees',{**updated,'leadership':'work_manager'})
        self.assertEqual(updated['leadership'],'work_manager');self.assertEqual(users,rows(self.conn,'SELECT * FROM users'))
    def test_migration_preserves_legacy_users_and_sessions(self):
        from db import ROOT
        legacy=connect(str(Path(self.tmp.name)/'legacy.sqlite'))
        for filename in ['001_initial.sql','002_period_layers.sql']:legacy.executescript((ROOT/'migrations'/filename).read_text())
        passwords=seed(legacy);_,token=service.login(legacy,dict(username='manager',password=passwords['manager']),'test')
        tables=['users','sessions','project_managers','employees','assignments','periods','events','audit']
        before={t:rows(legacy,f'SELECT * FROM {t}') for t in tables}
        migrate(legacy)
        for t in tables:
            after=rows(legacy,f'SELECT * FROM {t}')
            self.assertEqual(before[t],[{k:r[k] for k in before[t][0]} for r in after] if before[t] else after)
        self.assertEqual(service.authenticate(legacy,token)['username'],'manager')
        self.assertEqual(legacy.execute('PRAGMA foreign_keys').fetchone()[0],1)
        self.assertFalse(legacy.execute('PRAGMA foreign_key_check').fetchall());legacy.close()

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.old_db=os.environ.get('APP_DB');cls.old_origin=os.environ.get('APP_ORIGIN')
        os.environ['APP_DB']=str(Path(cls.tmp.name)/'http.sqlite');c=connect();migrate(c);cls.passwords=seed(c);c.close()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.port=cls.server.server_address[1]
        os.environ['APP_ORIGIN']=f'http://127.0.0.1:{cls.port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()
        for key,value in [('APP_DB',cls.old_db),('APP_ORIGIN',cls.old_origin)]:
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
    def request(self,path,data=None,cookie='',csrf='',origin=None,method=None):
        c=http.client.HTTPConnection('127.0.0.1',self.port);headers={}
        if cookie:headers['Cookie']=cookie
        if csrf:headers['X-CSRF-Token']=csrf
        if origin:headers['Origin']=origin
        if data is not None:headers['Content-Type']='application/json'
        c.request(method or ('POST' if data is not None else 'GET'),'/api/'+path,json.dumps(data) if data is not None else None,headers)
        r=c.getresponse();body=r.read();cookie=r.getheader('Set-Cookie');status=r.status;ctype=r.getheader('Content-Type');c.close()
        return status,json.loads(body) if 'json' in ctype else body,cookie
    def login(self,username='manager'):
        status,data,cookie=self.request('login',dict(username=username,password=self.passwords[username]));self.assertEqual(status,200);return cookie.split(';')[0],data['csrf']
    def test_login_logout_persistence_and_pdf_permissions(self):
        self.assertEqual(self.request('data')[0],401)
        cookie,csrf=self.login();status,data,_=self.request('data',cookie=cookie);self.assertEqual(status,200)
        p=next(p for p in data['periods'] if p['employee_id']==2)
        e=next(e for e in data['employees'] if e['id']==2)
        payload={**p,'schedule_version':e['schedule_version'],'notes':'Сохранено после повторного входа'}
        self.assertEqual(self.request('periods',payload,cookie,csrf)[0],200)
        self.assertEqual(self.request('export',dict(project_id=2,start='2026-01-01',end='2026-12-31'),cookie,csrf)[0],403)
        self.assertEqual(self.request('logout',{},cookie,csrf)[0],200);self.assertEqual(self.request('data',cookie=cookie)[0],401)
        cookie,csrf=self.login();_,data,_=self.request('data',cookie=cookie)
        self.assertEqual(next(v for v in data['periods'] if v['id']==p['id'])['notes'],payload['notes'])
        self.assertTrue(self.request('export',dict(project_id=1,start='2026-10-01',end='2026-10-31'),cookie,csrf)[1].startswith(b'%PDF'))
    def test_feedback_submission_and_admin_only_http_routes(self):
        cookie,csrf=self.login('manager');admin_cookie,admin_csrf=self.login('admin')
        _,raw=FeedbackTests.image(self)
        import base64
        image='data:image/png;base64,'+base64.b64encode(raw).decode()
        self.assertEqual(self.request('feedback',dict(message='CSRF'),cookie=cookie)[0],403)
        status,record,_=self.request('feedback',dict(kind='bug',message='Тест скриншота',screenshot=image),cookie,csrf)
        self.assertEqual(status,200)
        self.assertEqual(self.request('feedback',cookie=cookie)[0],403)
        self.assertEqual(self.request('feedback/'+str(record['id'])+'/screenshot',cookie=cookie)[0],403)
        self.assertEqual(self.request('feedback/'+str(record['id'])+'/screenshot',cookie=admin_cookie)[1],raw)
        status,records,_=self.request('feedback',cookie=admin_cookie);self.assertEqual(status,200)
        self.assertTrue(any(r['id']==record['id'] and r['has_screenshot'] for r in records))
        self.assertEqual(self.request('feedback-status',dict(id=record['id'],version=1,status='reviewed'),cookie,csrf)[0],403)
        self.assertEqual(self.request('feedback-status',dict(id=record['id'],version=1,status='reviewed'),admin_cookie,admin_csrf)[0],200)
    def test_feedback_accepts_screenshot_larger_than_one_megabyte(self):
        from PIL import Image
        import base64
        buffer=io.BytesIO();Image.frombytes('RGB',(800,500),os.urandom(800*500*3)).save(buffer,format='PNG')
        raw=buffer.getvalue();self.assertGreater(len(raw),1000000)
        cookie,csrf=self.login('manager')
        status,record,_=self.request('feedback',dict(kind='idea',message='Большой скриншот',screenshot='data:image/png;base64,'+base64.b64encode(raw).decode()),cookie,csrf)
        self.assertEqual(status,200)
        admin_cookie,_=self.login('admin');self.assertEqual(self.request('feedback/'+str(record['id'])+'/screenshot',cookie=admin_cookie)[1],raw)
    def test_employee_photo_http_and_atomic_invalid_creation(self):
        admin_cookie,admin_csrf=self.login('admin');manager_cookie,manager_csrf=self.login('manager')
        self.assertEqual(self.request('users',dict(username='photo-reviewer',name='Photo reviewer',role='manager',password='photo-reviewer-password',active=True),admin_cookie,admin_csrf)[0],200)
        status,_,login_cookie=self.request('login',dict(username='photo-reviewer',password='photo-reviewer-password'));self.assertEqual(status,200);other_cookie=login_cookie.split(';')[0]
        image,raw=FeedbackTests.image(self)
        _,data,_=self.request('data',cookie=admin_cookie);old=data['employees'][0]
        self.assertEqual(self.request('employees',{**old,'photo':image},admin_cookie,admin_csrf)[0],200)
        self.assertEqual(self.request('employees/'+str(old['id'])+'/photo',cookie=manager_cookie)[1],raw)
        self.assertEqual(self.request('employees/'+str(old['id'])+'/photo',cookie=other_cookie)[0],403)
        self.assertEqual(self.request('employees',{**old,'photo':None},manager_cookie,manager_csrf)[0],403)
        count=len(data['employees'])
        self.assertEqual(self.request('employees',dict(first_name='Тест',last_name='Фото',specialty='Монтажник',photo='invalid'),admin_cookie,admin_csrf)[0],400)
        _,data,_=self.request('data',cookie=admin_cookie);self.assertEqual(len(data['employees']),count)
    def test_two_simultaneous_editors(self):
        admin_cookie,admin_csrf=self.login('admin');manager_cookie,manager_csrf=self.login('manager')
        _,snapshot,_=self.request('data',cookie=manager_cookie)
        p=next(p for p in snapshot['periods'] if p['employee_id']==4)
        employee=next(e for e in snapshot['employees'] if e['id']==4)
        barrier=threading.Barrier(2);results=[]
        def change(cookie,csrf,note):
            barrier.wait()
            results.append(self.request('periods',{**p,'schedule_version':employee['schedule_version'],'notes':note},cookie,csrf)[0])
        threads=[threading.Thread(target=change,args=(admin_cookie,admin_csrf,'Администратор')),threading.Thread(target=change,args=(manager_cookie,manager_csrf,'Руководитель'))]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(sorted(results),[200,409])
    def test_worker_card_creation_is_atomic(self):
        cookie,csrf=self.login('admin')
        _,before,_=self.request('data',cookie=cookie)
        payload=dict(first_name='Тест',last_name='Неверный',specialty='Монтажник',assignment=dict(project_id=1,start='2028-01-01',end='2028-02-01'))
        self.assertEqual(self.request('employees',payload,cookie,csrf)[0],409)
        _,after,_=self.request('data',cookie=cookie)
        self.assertEqual(before['employees'],after['employees']);self.assertEqual(before['assignments'],after['assignments'])
    def test_csrf_and_origin(self):
        cookie,csrf=self.login()
        self.assertEqual(self.request('logout',{},cookie)[0],403)
        self.assertEqual(self.request('logout',{},cookie,csrf,origin='https://evil.example')[0],403)
    def test_disabled_account_loses_existing_session(self):
        cookie,csrf=self.login('other');admin_cookie,admin_csrf=self.login('admin');_,data,_=self.request('data',cookie=admin_cookie)
        user=next(u for u in data['users'] if u['username']=='other')
        self.assertEqual(self.request('users',{**user,'active':False},admin_cookie,admin_csrf)[0],200)
        self.assertEqual(self.request('data',cookie=cookie)[0],401)
        self.assertEqual(self.request('login',dict(username='other',password=self.passwords['other']))[0],401)
    def test_change_password_invalidates_session(self):
        cookie,csrf=self.login('admin');new='Test-password-only-2026'
        self.assertEqual(self.request('password',dict(current=self.passwords['admin'],password=new),cookie,csrf)[0],200)
        self.assertEqual(self.request('data',cookie=cookie)[0],401)
        self.assertEqual(self.request('login',dict(username='admin',password=new))[0],200)
        self.passwords['admin']=new

if __name__=='__main__':unittest.main(verbosity=2)
