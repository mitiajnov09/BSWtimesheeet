ALTER TABLE projects ADD COLUMN address TEXT NOT NULL DEFAULT '';
ALTER TABLE projects ADD COLUMN country TEXT NOT NULL DEFAULT '';
UPDATE projects SET
  address=(SELECT CASE WHEN trim(s.address)<>'' THEN s.address ELSE s.city END FROM sites s WHERE s.id=projects.site_id),
  country=(SELECT s.country FROM sites s WHERE s.id=projects.site_id);
INSERT INTO schema_migrations(version) VALUES(8);
