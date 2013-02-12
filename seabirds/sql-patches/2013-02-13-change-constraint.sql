
BEGIN;
ALTER TABLE "cms_post" DROP CONSTRAINT "section_id_refs_id_ac56f035";
DROP TABLE "cms_section";
COMMIT;
