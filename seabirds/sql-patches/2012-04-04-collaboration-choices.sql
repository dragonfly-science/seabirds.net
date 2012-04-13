BEGIN;
--CREATE TABLE "profile_collaborationchoice" (
--    "id" serial NOT NULL PRIMARY KEY,
--    "label" varchar(50) NOT NULL,
--    "description" text NOT NULL
--)
--;
CREATE TABLE "profile_userprofile_collaboration_choices" (
    "id" serial NOT NULL PRIMARY KEY,
    "userprofile_id" integer NOT NULL,
    "collaborationchoice_id" integer NOT NULL REFERENCES "profile_collaborationchoice" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("userprofile_id", "collaborationchoice_id")
)
;
ALTER TABLE "profile_userprofile_collaboration_choices" ADD CONSTRAINT "userprofile_id_refs_id_93a0b550" FOREIGN KEY ("userprofile_id") REFERENCES "profile_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED;
--ALTER TABLE "profile_userprofile_seabirds" ADD CONSTRAINT "userprofile_id_refs_id_9bfb80d6" FOREIGN KEY ("userprofile_id") REFERENCES "profile_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;

