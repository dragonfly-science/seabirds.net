BEGIN;
ALTER TABLE cms_post DROP COLUMN _notify_moderator;
COMMIT;
