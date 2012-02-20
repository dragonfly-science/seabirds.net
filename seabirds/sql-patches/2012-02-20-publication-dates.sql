BEGIN;
ALTER TABLE "cms_page" ADD COLUMN "date_published" date;
ALTER TABLE "cms_page" ADD COLUMN  "date_created" date NOT NULL DEFAULT '2012-01-01'::DATE;
ALTER TABLE "cms_page" ADD COLUMN    "date_updated" date NOT NULL DEFAULT '2012-01-01'::DATE;
    
ALTER TABLE "cms_post" ALTER COLUMN "date_published" DROP NOT NULL;
ALTER TABLE "cms_post" ADD COLUMN  "date_created" date NOT NULL DEFAULT '2012-01-01'::DATE;
ALTER TABLE "cms_post" ADD COLUMN    "date_updated" date NOT NULL DEFAULT '2012-01-01'::DATE;
ALTER TABLE "cms_post" DROP COLUMN    "retracted";

ALTER TABLE "cms_image" RENAME COLUMN  "date_modified" TO "date_updated";

ALTER TABLE "profile_userprofile" ADD COLUMN  "date_created" date NOT NULL DEFAULT '2012-01-01'::DATE;
ALTER TABLE "profile_userprofile" ADD COLUMN    "date_updated" date NOT NULL DEFAULT '2012-01-01'::DATE;

COMMIT;
