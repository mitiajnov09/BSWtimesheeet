BEGIN IMMEDIATE;
ALTER TABLE events ADD COLUMN transport TEXT NOT NULL DEFAULT 'plane' CHECK(transport IN ('plane','car','ferry'));
INSERT INTO schema_migrations(version) VALUES(5);
COMMIT;
