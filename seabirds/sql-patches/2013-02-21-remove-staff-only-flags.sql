BEGIN;
    ALTER TABLE "cms_listing" DROP COLUMN "staff_only_read";
    ALTER TABLE "cms_listing" DROP COLUMN "staff_only_write";
COMMIT;
