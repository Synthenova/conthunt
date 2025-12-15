-- Migration: Add user roles
-- Supports: free, creator, pro_research
SET search_path = conthunt, public;

-- Add role column with enum constraint and default to 'free'
ALTER TABLE conthunt.users 
ADD COLUMN role TEXT NOT NULL DEFAULT 'free'
CHECK (role IN ('free', 'creator', 'pro_research'));

-- Index for efficient role-based queries
CREATE INDEX idx_users_role ON conthunt.users(role);
