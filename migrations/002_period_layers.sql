ALTER TABLE periods ADD COLUMN layer INTEGER NOT NULL DEFAULT 0 CHECK(layer BETWEEN 0 AND 31);
CREATE INDEX period_layer_range ON periods(employee_id,layer,start,end);
INSERT INTO schema_migrations(version) VALUES(2);
