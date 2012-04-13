BEGIN;

--CREATE TABLE "cms_section" (
--    "id" serial NOT NULL PRIMARY KEY,
--    "key" varchar(50) NOT NULL,
--    "description" text NOT NULL,
--    "staff_only_write" boolean NOT NULL,
--    "staff_only_read" boolean NOT NULL,
--    "allow_comments" boolean NOT NULL
--)
--;

INSERT INTO "cms_section" VALUES (1, 'discussion', 'Member discussion', FALSE, FALSE, TRUE);
INSERT INTO "cms_section" VALUES (2, 'news', 'WSU news', TRUE, FALSE, TRUE);
INSERT INTO "cms_section" VALUES (3, 'staff', 'Staff only discussion', TRUE, TRUE, TRUE);


ALTER TABLE "cms_post" ADD COLUMN "enable_comments" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE "cms_post" ADD COLUMN "section_id" integer NOT NULL DEFAULT 1;
ALTER TABLE "cms_post" ALTER COLUMN "enable_comments" DROP DEFAULT;

ALTER TABLE "cms_post" ADD CONSTRAINT "section_id_refs_id_ac56f035" FOREIGN KEY ("section_id") REFERENCES "cms_section" ("id") DEFERRABLE INITIALLY DEFERRED;

COMMIT;
