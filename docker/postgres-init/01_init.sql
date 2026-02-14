-- Keep this light: schema + a couple common extensions.
-- The rest of the DB shape is created by Alembic migrations.

CREATE SCHEMA IF NOT EXISTS conthunt AUTHORIZATION conthunt_service;
GRANT USAGE ON SCHEMA conthunt TO conthunt_service;
GRANT CREATE ON SCHEMA conthunt TO conthunt_service;

-- Some legacy migrations grant to this role. Keep it around locally.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'conthunt_app') THEN
    CREATE ROLE conthunt_app LOGIN PASSWORD 'conthunt_local';
  END IF;
END
$$;

-- Default search_path for app roles (matches how the app expects to run).
ALTER ROLE conthunt_service SET search_path = conthunt, public;
ALTER ROLE conthunt_app SET search_path = conthunt, public;

-- Optional but commonly used; harmless if unused.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
