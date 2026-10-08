import io, sqlite3, unittest
from pathlib import Path
from pypdf import PdfReader
import test_app
from db import ROOT, seed, migrate, rows
from domain import Problem
from pdf_export import export
import service

class TravelBookingTests(unittest.TestCase):
    setUp=test_app.DatabaseTests.setUp
    tearDown=test_app.DatabaseTests.tearDown

    def test_new_trip_is_unknown_and_unbooked_even_with_flight_number(self):
        trip=service.save_event(self.conn,self.manager,dict(project_id=1,employee_id=1,date='2026-10-08',kind='outbound',flight='SK123'))
        self.assertEqual((trip['transport'],trip['ticket_bought']),('unknown',0))

    def test_booking_and_transport_preserve_schedule_and_use_versions(self):
        before=service.employee_periods(self.conn,1)
        trip=service.get(self.conn,'events',1)
        for transport in ['unknown','car','ferry','plane']:
            trip=service.save_event(self.conn,self.manager,{**trip,'transport':transport,'ticket_bought':True})
            self.assertEqual((trip['transport'],trip['ticket_bought']),(transport,1))
        old=trip
        trip=service.save_event(self.conn,self.manager,{**trip,'ticket_bought':0})
        self.assertEqual(trip['ticket_bought'],0)
        with self.assertRaises(Problem) as ctx:service.save_event(self.conn,self.manager,{**old,'ticket_bought':1})
        self.assertEqual(ctx.exception.status,409)
        self.assertEqual(before,service.employee_periods(self.conn,1))
        for invalid in ['false','1',2,-1,None,[],1.0]:
            with self.assertRaises(Problem):service.save_event(self.conn,self.manager,{**trip,'ticket_bought':invalid})

    def test_pdf_exports_unknown_and_booking_in_every_language(self):
        trip=service.get(self.conn,'events',1)
        trip=service.save_event(self.conn,self.manager,{**trip,'transport':'unknown','ticket_bought':1})
        for language,transport,ticket in [('en','Transport not selected','Ticket purchased'),('lt','Transportas nepasirinktas','Bilietas nupirktas'),('pl','Transport niewybrany','Bilet kupiony'),('ru','Транспорт не выбран','Билет куплен')]:
            pdf=export(self.conn,self.manager,dict(project_id=1,start='2026-10-01',end='2026-10-31',employee_ids=[1],language=language))
            reader=PdfReader(io.BytesIO(pdf));text=''.join(page.extract_text() for page in reader.pages)
            self.assertIn(transport,text);self.assertIn(ticket,text)

    def test_migration_preserves_every_existing_event_field_and_index(self):
        conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
        try:
            for path in sorted((ROOT/'migrations').glob('*.sql')):
                if int(path.name.split('_')[0])<10:conn.executescript(path.read_text())
            seed(conn)
            conn.execute("UPDATE events SET transport='ferry',route='VNO → ARN',notes='Keep me',version=7 WHERE id=1")
            conn.commit();before=rows(conn,'SELECT * FROM events ORDER BY id')
            migrate(conn)
            after=rows(conn,'SELECT * FROM events ORDER BY id')
            self.assertEqual([{k:v for k,v in row.items() if k!='ticket_bought'} for row in after],before)
            self.assertTrue(all(row['ticket_bought']==0 for row in after))
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertFalse(conn.execute('PRAGMA foreign_key_check').fetchall())
            self.assertTrue(conn.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='event_range'").fetchone())
            migrate(conn)
            self.assertEqual(rows(conn,'SELECT * FROM events ORDER BY id'),after)
        finally:conn.close()
