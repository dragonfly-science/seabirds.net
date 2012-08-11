BEGIN;
ALTER TABLE profile_userprofile ADD COLUMN "is_moderator" boolean NOT NULL DEFAULT FALSE;

COMMIT;
