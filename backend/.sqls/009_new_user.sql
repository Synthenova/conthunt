-- 1. Create the Service Role
-- (Using 'IF NOT EXISTS' avoids errors if you run it twice)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'conthunt_service') THEN
    CREATE ROLE conthunt_service WITH LOGIN PASSWORD 'PLACEHOLDER_CHANGE_ME_MANUALLY';
  END IF;
END
$$;

-- 2. Grant Connection & Usage
-- NOTE: Changed database from 'conthunt' to 'postgres' based on your previous errors
GRANT CONNECT ON DATABASE postgres TO conthunt_service;
GRANT USAGE ON SCHEMA conthunt TO conthunt_service;

-- 3. Grant Permissions on EXISTING tables/sequences
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA conthunt TO conthunt_service;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA conthunt TO conthunt_service;

-- 4. [CRITICAL] Future-Proofing
-- Ensures any NEW table you create later automatically gives permission to this user
ALTER DEFAULT PRIVILEGES IN SCHEMA conthunt 
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO conthunt_service;

ALTER DEFAULT PRIVILEGES IN SCHEMA conthunt 
GRANT USAGE, SELECT ON SEQUENCES TO conthunt_service;

-- 5. Fix RLS on Users Table
ALTER TABLE conthunt.users ENABLE ROW LEVEL SECURITY;

-- Remove conflicting policies first to ensure clean state
DROP POLICY IF EXISTS users_select_service ON conthunt.users;
DROP POLICY IF EXISTS users_insert_service ON conthunt.users;
DROP POLICY IF EXISTS users_update_service ON conthunt.users;
DROP POLICY IF EXISTS users_delete_service ON conthunt.users;

-- 6. Apply "Service Account" Policies (Allow All for this specific user)
-- This allows the backend to Login (Select) and Signup (Insert) without restriction.

CREATE POLICY users_select_service ON conthunt.users
FOR SELECT TO conthunt_service USING (true);

CREATE POLICY users_insert_service ON conthunt.users
FOR INSERT TO conthunt_service WITH CHECK (true);

CREATE POLICY users_update_service ON conthunt.users
FOR UPDATE TO conthunt_service USING (true);

CREATE POLICY users_delete_service ON conthunt.users
FOR DELETE TO conthunt_service USING (true);

-- 7. (Optional) Apply similar "Allow All" policies for other tables if needed
-- Since you are creating a trusted service user, you likely want RLS 
-- to allow this user to access Boards/Searches/Chats too.
-- Let me know if you need the loop command to apply "USING (true)" to all other tables.