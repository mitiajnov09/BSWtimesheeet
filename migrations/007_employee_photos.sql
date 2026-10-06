BEGIN IMMEDIATE;
CREATE TABLE employee_photos(employee_id INTEGER PRIMARY KEY REFERENCES employees(id),content BLOB NOT NULL,mime TEXT NOT NULL);
INSERT INTO schema_migrations(version) VALUES(7);
COMMIT;
