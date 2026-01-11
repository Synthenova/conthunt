-- Set current_period_start for existing users
SET search_path = conthunt, public;

-- Disable RLS on users table
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

UPDATE users 
SET current_period_start = NOW()::date 
WHERE current_period_start IS NULL;

-- Re-enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
