BEGIN;
ALTER TABLE pigeonpost_pigeon ADD COLUMN "send_to_id" integer;
ALTER TABLE pigeonpost_pigeon ADD COLUMN "send_to_method" text;
COMMIT;
