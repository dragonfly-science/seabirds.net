BEGIN;
DROP TABLE IF EXISTS "pigeonpost_pigeon" CASCADE;
DROP TABLE IF EXISTS "pigeonpost_outbox" CASCADE;
CREATE TABLE "pigeonpost_pigeon" (
    "id" serial NOT NULL PRIMARY KEY,
    "source_content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
    "source_id" integer CHECK ("source_id" >= 0) NOT NULL,
    "successes" integer NOT NULL,
    "failures" integer NOT NULL,
    "to_send" boolean NOT NULL,
    "sent_at" timestamp with time zone,
    "render_email_method" text NOT NULL,
    "scheduled_for" timestamp with time zone NOT NULL,
    UNIQUE ("source_content_type_id", "source_id")
)
;
CREATE TABLE "pigeonpost_outbox" (
    "id" serial NOT NULL PRIMARY KEY,
    "pigeon_id" integer REFERENCES "pigeonpost_pigeon" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "message" text NOT NULL,
    "sent_at" timestamp with time zone,
    "succeeded" boolean NOT NULL,
    "failures" integer NOT NULL,
    UNIQUE ("pigeon_id", "user_id")
)
;
COMMIT;

