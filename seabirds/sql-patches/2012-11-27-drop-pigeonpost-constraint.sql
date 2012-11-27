BEGIN;
ALTER TABLE pigeonpost_pigeon DROP CONSTRAINT "pigeonpost_pigeon_source_content_type_id_source_id_key";
COMMIT;
