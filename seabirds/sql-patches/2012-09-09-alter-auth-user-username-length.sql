BEGIN;
ALTER TABLE "auth_user" ALTER COLUMN "username" TYPE character varying(75);
COMMIT;
