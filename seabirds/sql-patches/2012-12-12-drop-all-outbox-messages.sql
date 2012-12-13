BEGIN;
DELETE FROM pigeonpost_outbox *;
ALTER SEQUENCE pigeonpost_outbox_id_seq RESTART WITH 1;
COMMIT;
