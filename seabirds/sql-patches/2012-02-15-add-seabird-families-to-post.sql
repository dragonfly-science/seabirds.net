BEGIN;
CREATE TABLE "cms_post_seabird_families" (
    "id" serial NOT NULL PRIMARY KEY,
    "post_id" integer NOT NULL,
    "seabirdfamily_id" integer NOT NULL REFERENCES "categories_seabirdfamily" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("post_id", "seabirdfamily_id")
)
;
ALTER TABLE "cms_post" ADD COLUMN  "retracted" boolean NOT NULL DEFAULT FALSE;
ALTER TABLE "cms_post_seabird_families" ADD CONSTRAINT "post_id_refs_id_642989da" FOREIGN KEY ("post_id") REFERENCES "cms_post" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;
