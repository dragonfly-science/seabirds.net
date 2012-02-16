BEGIN;
CREATE TABLE "cms_image_seabird_families" (
    "id" serial NOT NULL PRIMARY KEY,
    "image_id" integer NOT NULL,
    "seabirdfamily_id" integer NOT NULL REFERENCES "categories_seabirdfamily" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("image_id", "seabirdfamily_id")
);
ALTER TABLE "cms_image_seabird_families" ADD CONSTRAINT "image_id_refs_id_980bc4a2" FOREIGN KEY ("image_id") REFERENCES "cms_image" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;
