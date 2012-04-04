BEGIN;
ALTER TABLE "profile_userprofile" ADD COLUMN "twitter" character(16);
ALTER TABLE "profile_userprofile" ADD COLUMN "display_twitter" boolean;
COMMIT;
