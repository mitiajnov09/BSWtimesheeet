BEGIN IMMEDIATE;
CREATE TABLE feedback_rate_events(
 id INTEGER PRIMARY KEY,
 user_id INTEGER NOT NULL REFERENCES users(id),
 created_at INTEGER NOT NULL
);
CREATE INDEX feedback_rate_user_time ON feedback_rate_events(user_id,created_at);
CREATE INDEX feedback_rate_time ON feedback_rate_events(created_at);
CREATE INDEX feedback_user_status ON feedback(user_id,status);
INSERT INTO schema_migrations(version) VALUES(9);
COMMIT;
