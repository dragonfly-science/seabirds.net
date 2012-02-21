BEGIN;

CREATE TABLE "cms_post_section" (
    "id" serial NOT NULL PRIMARY KEY,
    "post_id" integer NOT NULL,
    "section_id" integer NOT NULL,
    UNIQUE ("post_id", "section_id")
);

ALTER TABLE "cms_post" ADD COLUMN "enable_comments" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE "cms_post" ALTER COLUMN "enable_comments" DROP DEFAULT;

CREATE TABLE "cms_section" (
    "id" serial NOT NULL PRIMARY KEY,
    "key" varchar(50) NOT NULL,
    "description" text NOT NULL,
    "staff_only_write" boolean NOT NULL,
    "staff_only_read" boolean NOT NULL,
    "allow_comments" boolean NOT NULL
);

ALTER TABLE "cms_post_section" ADD CONSTRAINT "post_id_refs_id_86c5b23f" FOREIGN KEY ("post_id") REFERENCES "cms_post" ("id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "cms_post_section" ADD CONSTRAINT "section_id_refs_id_cf468409" FOREIGN KEY ("section_id") REFERENCES "cms_section" ("id") DEFERRABLE INITIALLY DEFERRED;

INSERT INTO "cms_section" VALUES (1, 'discussion', 'Member discssion', FALSE, FALSE, TRUE);
INSERT INTO "cms_section" VALUES (2, 'news', 'WSU news', TRUE, FALSE, TRUE);
INSERT INTO "cms_section" VALUES (3, 'staff', 'Staff only discussion', TRUE, TRUE, TRUE);

INSERT INTO "cms_post_section" ("post_id", "section_id") SELECT id, 1 FROM "cms_post";
COMMIT;
