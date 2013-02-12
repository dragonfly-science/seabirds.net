
BEGIN;
ALTER TABLE "cms_post" DROP CONSTRAINT "section_id_refs_id_ac56f035";
DROP TABLE "cms_section";
ALTER TABLE "cms_post" ADD CONSTRAINT "listing_id_refs_id_e67965c0" FOREIGN KEY ("listing_id") REFERENCES "cms_listing" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;
