BEGIN IMMEDIATE;
CREATE TABLE events_v10(
 id INTEGER PRIMARY KEY,
 project_id INTEGER NOT NULL REFERENCES projects(id),
 employee_id INTEGER NOT NULL REFERENCES employees(id),
 date TEXT NOT NULL,
 time TEXT NOT NULL DEFAULT '',
 timezone TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('outbound','return','arrival','departure','note')),
 route TEXT NOT NULL DEFAULT '',
 flight TEXT NOT NULL DEFAULT '',
 notes TEXT NOT NULL DEFAULT '',
 version INTEGER NOT NULL DEFAULT 1,
 transport TEXT NOT NULL DEFAULT 'unknown' CHECK(transport IN ('unknown','plane','car','ferry')),
 ticket_bought INTEGER NOT NULL DEFAULT 0 CHECK(ticket_bought IN (0,1))
);
INSERT INTO events_v10(id,project_id,employee_id,date,time,timezone,kind,route,flight,notes,version,transport)
 SELECT id,project_id,employee_id,date,time,timezone,kind,route,flight,notes,version,transport FROM events;
DROP TABLE events;
ALTER TABLE events_v10 RENAME TO events;
CREATE INDEX event_range ON events(project_id,date);
INSERT INTO schema_migrations(version) VALUES(10);
COMMIT;
