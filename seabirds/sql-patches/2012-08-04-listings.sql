BEGIN;
DROP TABLE IF EXISTS cms_listing CASCADE;
ALTER TABLE cms_section RENAME TO cms_listing;
ALTER TABLE cms_listing ADD  "primary_list" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE cms_post RENAME section_id tO listing_id;
ALTER TABLE "cms_post" ADD CONSTRAINT "listing_id_refs_id_e67965c0" FOREIGN KEY ("listing_id") REFERENCES "cms_listing" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "profile_userprofile_subscriptions" (
    "id" serial NOT NULL PRIMARY KEY,
    "userprofile_id" integer NOT NULL,
    "listing_id" integer NOT NULL,
    UNIQUE ("userprofile_id", "listing_id")
)
;

ALTER TABLE "profile_userprofile_subscriptions" ADD CONSTRAINT "userprofile_id_refs_id_30bf6074" FOREIGN KEY ("userprofile_id") REFERENCES "profile_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "profile_userprofile_subscriptions" ADD CONSTRAINT "listing_id_refs_id_6088e18" FOREIGN KEY ("listing_id") REFERENCES "cms_listing" ("id") DEFERRABLE INITIALLY DEFERRED;

COMMIT;
