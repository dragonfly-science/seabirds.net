BEGIN;

CREATE TABLE "categories_researchfield" (
    "id" serial NOT NULL PRIMARY KEY,
    "choice" varchar(60) NOT NULL
);

CREATE TABLE "profile_userprofile_research_field" (
    "id" serial NOT NULL PRIMARY KEY,
    "userprofile_id" integer NOT NULL,
    "researchfield_id" integer NOT NULL REFERENCES "categories_researchfield" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("userprofile_id", "researchfield_id")
);

INSERT INTO "categories_researchfield" VALUES (1, 'Not a researcher');
INSERT INTO "categories_researchfield" VALUES (2, 'Behaviour');
INSERT INTO "categories_researchfield" VALUES (3, 'Ecology');
INSERT INTO "categories_researchfield" VALUES (4, 'Evolution');
INSERT INTO "categories_researchfield" VALUES (5, 'Genetics');
INSERT INTO "categories_researchfield" VALUES (6, 'Parasitology');
INSERT INTO "categories_researchfield" VALUES (7, 'Physiology');
INSERT INTO "categories_researchfield" VALUES (8, 'Taxonomy');
COMMIT;
