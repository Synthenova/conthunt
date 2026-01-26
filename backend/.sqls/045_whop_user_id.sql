-- Add whop_user_id column to users table for linking Whop identities

SET search_path = conthunt, public;
ALTER TABLE users ADD COLUMN IF NOT EXISTS whop_user_id VARCHAR(255) UNIQUE DEFAULT NULL;
