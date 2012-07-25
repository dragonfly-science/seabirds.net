BEGIN;
ALTER TABLE "profile_userprofile" ADD COLUMN "is_researcher" boolean NOT NULL DEFAULT TRUE;

UPDATE profile_userprofile
SET is_researcher = TRUE
WHERE profile_userprofile.id != -1;

COMMIT;
