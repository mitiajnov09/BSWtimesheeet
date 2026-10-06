BEGIN IMMEDIATE;
CREATE TABLE feedback(
 id INTEGER PRIMARY KEY,
 user_id INTEGER NOT NULL REFERENCES users(id),
 project_id INTEGER REFERENCES projects(id),
 kind TEXT NOT NULL CHECK(kind IN ('bug','idea')),
 message TEXT NOT NULL,
 screenshot BLOB,
 screenshot_type TEXT,
 status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','reviewed')),
 version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX feedback_created ON feedback(id DESC);
INSERT INTO schema_migrations(version) VALUES(6);
COMMIT;
