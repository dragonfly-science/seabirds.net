BEGIN;
    ALTER TABLE "cms_listing" ADD COLUMN "post_permission_id" integer REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE "cms_listing" ADD COLUMN "read_permission_id" integer REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE "cms_listing" ADD COLUMN "moderation_permission_id" integer REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;

