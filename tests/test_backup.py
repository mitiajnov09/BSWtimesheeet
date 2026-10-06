import sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from db import connect,migrate
from backup import create_backup
from restore import restore_backup

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.source=self.root/'live.sqlite3';self.conn=connect(str(self.source));migrate(self.conn)
        self.conn.execute("INSERT INTO users(username,name,password_hash,role) VALUES('test','Test','unused','admin')")
        self.conn.execute("INSERT INTO employees(first_name,last_name,specialty) VALUES('Jonas','Test','Electrician')")
        self.conn.execute("INSERT INTO employee_photos VALUES(1,?,'image/png')",(b'portrait-bytes',))
        self.conn.execute("INSERT INTO feedback(user_id,kind,message,screenshot,screenshot_type) VALUES(1,'idea','Suggestion',?,'image/png')",(b'screenshot-bytes',))
        self.conn.commit()
    def tearDown(self):self.conn.close();self.tmp.cleanup()
    def test_online_wal_backup_includes_photos_and_feedback(self):
        self.conn.execute("UPDATE employees SET first_name='Mantas'");self.conn.commit()
        destination=self.root/'copies'/'copy.sqlite3';create_backup(self.source,destination)
        c=sqlite3.connect(destination)
        self.assertEqual(c.execute('SELECT first_name FROM employees').fetchone()[0],'Mantas')
        self.assertEqual(c.execute('SELECT content FROM employee_photos').fetchone()[0],b'portrait-bytes')
        self.assertEqual(c.execute('SELECT screenshot FROM feedback').fetchone()[0],b'screenshot-bytes')
        self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok');c.close()
        self.assertEqual(destination.stat().st_mode&0o777,0o600)
    def test_existing_backup_and_missing_source_are_not_overwritten(self):
        destination=self.root/'keep';destination.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):create_backup(self.source,destination)
        self.assertEqual(destination.read_bytes(),b'keep')
        with self.assertRaises(ValueError):create_backup(self.root/'missing',self.root/'unused')
        self.assertFalse((self.root/'missing').exists());self.assertFalse((self.root/'unused').exists())
    def test_restore_preserves_content_and_requires_explicit_replacement(self):
        copy=self.root/'copy.sqlite3';create_backup(self.source,copy)
        target=self.root/'restored.sqlite3';restore_backup(copy,target)
        c=sqlite3.connect(target);c.execute("UPDATE employees SET first_name='Changed'");c.commit();c.close()
        with self.assertRaises(ValueError):restore_backup(copy,target)
        restore_backup(copy,target,replace=True)
        c=sqlite3.connect(target);self.assertEqual(c.execute('SELECT first_name FROM employees').fetchone()[0],'Jonas')
        self.assertEqual(c.execute('SELECT screenshot FROM feedback').fetchone()[0],b'screenshot-bytes');c.close()
    def test_invalid_copy_does_not_change_destination(self):
        target=self.root/'restored.sqlite3';create_backup(self.source,target);before=target.read_bytes()
        unrelated=self.root/'unrelated.sqlite3';c=sqlite3.connect(unrelated);c.execute('CREATE TABLE something(id)');c.commit();c.close()
        with self.assertRaises(ValueError):restore_backup(unrelated,target,replace=True)
        self.assertEqual(target.read_bytes(),before)
        damaged=self.root/'damaged';damaged.write_bytes(b'not sqlite')
        with self.assertRaises(sqlite3.Error):restore_backup(damaged,target,replace=True)
        self.assertEqual(target.read_bytes(),before)
    def test_cli_works_without_installed_site_packages(self):
        project=Path(__file__).resolve().parents[1];copy=self.root/'cli.sqlite3';target=self.root/'cli-restored.sqlite3'
        subprocess.run([sys.executable,'-S',str(project/'backup.py'),str(copy),'--database',str(self.source)],check=True,capture_output=True)
        subprocess.run([sys.executable,'-S',str(project/'restore.py'),str(copy),'--database',str(target)],check=True,capture_output=True)
        c=sqlite3.connect(target);self.assertEqual(c.execute('SELECT message FROM feedback').fetchone()[0],'Suggestion');c.close()

if __name__=='__main__':unittest.main()
