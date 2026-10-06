BEGIN IMMEDIATE;
ALTER TABLE teams ADD COLUMN status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived'));
ALTER TABLE assignments ADD COLUMN active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1));
ALTER TABLE employees ADD COLUMN leadership TEXT NOT NULL DEFAULT 'none' CHECK(leadership IN ('none','team_leader','work_manager'));
INSERT INTO schema_migrations(version) VALUES(4);
COMMIT;
