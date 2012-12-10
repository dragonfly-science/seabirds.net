BEGIN;
ALTER TABLE "profile_userprofile" ADD COLUMN "is_valid_seabirder" boolean NOT NULL DEFAULT FALSE;
COMMIT;
