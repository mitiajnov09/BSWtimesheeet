"""Security boundaries for bounded feedback storage, pages and deletion."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feedback
import service
from db import connect,migrate,seed,insert
from domain import Problem


class FeedbackSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.conn=connect(Path(self.tmp.name)/'feedback.sqlite3');migrate(self.conn);seed(self.conn)
        self.admin=service.get(self.conn,'users',1);self.manager=service.get(self.conn,'users',2)

    def tearDown(self):
        self.conn.close();self.tmp.cleanup()

    def add(self,user=None,**changes):
        return insert(self.conn,'feedback',dict(user_id=(user or self.manager)['id'],kind='bug',message='private test message',**changes))

    def fails(self,status,operation):
        with self.assertRaises(Problem) as error:operation()
        self.assertEqual(error.exception.status,status)

    def test_rate_survives_deletion_and_expires_after_hour(self):
        with patch('feedback.time.time',return_value=10000):
            for _ in range(5):feedback.submit(self.conn,self.manager,{'message':'test'})
            self.fails(429,lambda:feedback.submit(self.conn,self.manager,{'message':'sixth'}))
            record=service.get(self.conn,'feedback',1)
            feedback.remove(self.conn,self.admin,{'id':1,'version':record['version']})
            self.fails(429,lambda:feedback.submit(self.conn,self.manager,{'message':'after delete'}))
        with patch('feedback.time.time',return_value=13600):
            feedback.submit(self.conn,self.manager,{'message':'next hour'})
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM feedback_rate_events').fetchone()[0],1)

    def test_rate_separates_users(self):
        for _ in range(5):feedback.submit(self.conn,self.manager,{'message':'test'})
        self.assertTrue(feedback.submit(self.conn,self.admin,{'message':'different user'})['ok'])

    def test_pending_and_total_record_limits_preserve_existing(self):
        for _ in range(100):self.add()
        self.fails(429,lambda:feedback.submit(self.conn,self.manager,{'message':'overflow'}))
        self.conn.execute("UPDATE feedback SET status='reviewed'")
        feedback.submit(self.conn,self.manager,{'message':'after review'})
        with patch('feedback.MAX_TOTAL_RECORDS',101):
            self.fails(429,lambda:feedback.submit(self.conn,self.admin,{'message':'global overflow'}))
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0],101)

    def test_reopen_obeys_pending_limit(self):
        for _ in range(100):self.add()
        id=self.add(status='reviewed')
        self.fails(429,lambda:feedback.set_status(self.conn,self.admin,{'id':id,'version':1,'status':'new'}))
        self.assertEqual(service.get(self.conn,'feedback',id)['status'],'reviewed')

    def test_normalized_image_quota_counts_all_statuses(self):
        self.add(status='reviewed',screenshot=b'x'*20,screenshot_type='image/png')
        with patch('feedback.decode',return_value=(b'y'*10,'image/png')),patch('feedback.MAX_USER_IMAGES',25):
            self.fails(413,lambda:feedback.submit(self.conn,self.manager,{'message':'too much','screenshot':'encoded'}))
            self.assertTrue(feedback.submit(self.conn,self.manager,{'message':'no image'})['ok'])
        with patch('feedback.decode',return_value=(b'y'*10,'image/png')),patch('feedback.MAX_TOTAL_IMAGES',25):
            self.fails(413,lambda:feedback.submit(self.conn,self.admin,{'message':'global image overflow','screenshot':'encoded'}))
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM feedback WHERE screenshot IS NOT NULL').fetchone()[0],1)

    def test_inbox_pages_filtered_server_side_and_no_blobs(self):
        for i in range(125):self.add(status='reviewed' if i%2 else 'new',screenshot=b'image',screenshot_type='image/png')
        first=feedback.inbox(self.conn,self.admin)
        self.assertEqual((first['total'],len(first['items']),first['page_size']),(125,50,50))
        second=feedback.inbox(self.conn,self.admin,page=2)
        self.assertFalse({r['id'] for r in first['items']}&{r['id'] for r in second['items']})
        filtered=feedback.inbox(self.conn,self.admin,page=999,status='reviewed')
        self.assertEqual((filtered['total'],filtered['page'],len(filtered['items'])),(62,2,12))
        self.assertTrue(all(r['status']=='reviewed' for r in filtered['items']))
        self.assertNotIn('screenshot',first['items'][0])
        self.fails(403,lambda:feedback.inbox(self.conn,self.manager))
        for page in [0,-1,True,'bad',100001]:self.fails(400,lambda:feedback.inbox(self.conn,self.admin,page))
        self.fails(400,lambda:feedback.inbox(self.conn,self.admin,status='bad'))

    def test_delete_requires_admin_version_and_audit_has_only_metadata(self):
        id=self.add(project_id=1,screenshot=b'secret-image',screenshot_type='image/png')
        self.fails(403,lambda:feedback.remove(self.conn,self.manager,{'id':id,'version':1}))
        self.fails(409,lambda:feedback.remove(self.conn,self.admin,{'id':id,'version':0}))
        self.assertTrue(feedback.remove(self.conn,self.admin,{'id':id,'version':1})['ok'])
        self.assertIsNone(self.conn.execute('SELECT id FROM feedback WHERE id=?',(id,)).fetchone())
        audit=self.conn.execute("SELECT before_json,after_json FROM audit WHERE entity='feedback' AND entity_id=?",(id,)).fetchone()
        metadata=json.loads(audit['before_json'])
        self.assertNotIn('message',metadata);self.assertNotIn('screenshot',metadata)
        self.assertEqual(metadata['has_screenshot'],1);self.assertIsNone(audit['after_json'])
        self.assertFalse(any(row['entity']=='feedback' for row in service.history(self.conn,self.manager)))
        self.fails(404,lambda:feedback.remove(self.conn,self.admin,{'id':id,'version':1}))

    def test_deleted_highest_id_is_not_reused_by_new_submission(self):
        first=feedback.submit(self.conn,self.manager,{'message':'old record'})
        feedback.remove(self.conn,self.admin,{'id':first['id'],'version':1})
        second=feedback.submit(self.conn,self.manager,{'message':'new record'})
        self.assertGreater(second['id'],first['id'])
        self.fails(404,lambda:feedback.remove(self.conn,self.admin,{'id':first['id'],'version':1}))
        self.assertEqual(service.get(self.conn,'feedback',second['id'])['message'],'new record')

    def test_migration_idempotent_and_feedback_preserved(self):
        id=self.add();self.conn.commit();migrate(self.conn)
        self.assertEqual(service.get(self.conn,'feedback',id)['message'],'private test message')
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM schema_migrations WHERE version=9').fetchone()[0],1)


if __name__=='__main__':unittest.main()
