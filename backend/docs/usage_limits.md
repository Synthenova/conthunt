# Usage Limits & Plans Documentation

This document explains how to manage usage limits, add new plans, and configure feature quotas using SQL.

## Overview

Usage tracking is built on two tables:
1.  **`usage_logs`**: Records every time a user uses a feature (e.g., uses Gemini Analysis).
2.  **`plan_limits`**: Defines the maximum allowed usage for a specific **Role**, **Feature**, and **Period**.

The system is additive: if you define multiple limits for the same role/feature (e.g., both a Daily limit and a Monthly limit), the user is blocked if **ANY** of them are exceeded.

## Managing Limits with SQL

All configuration happens in the `plan_limits` table. You can run these SQL commands via your database client or modify the migration files.

### 1. View Current Limits
To see all active limits:
```sql
SELECT * FROM plan_limits ORDER BY plan_role, feature;
```

### 2. Add or Update a Limit
Use `INSERT ... ON CONFLICT` to safely set a limit. If it exists, it updates; if not, it creates.

**Example: Set 'Creator' plan to 50 analysis calls per month**
```sql
INSERT INTO plan_limits (plan_role, feature, period, limit_count) 
VALUES ('creator', 'gemini_analysis', 'monthly', 50)
ON CONFLICT (plan_role, feature, period) 
DO UPDATE SET limit_count = EXCLUDED.limit_count;
```

**Example: Set 'Free' plan to 10 analysis calls per day**
```sql
INSERT INTO plan_limits (plan_role, feature, period, limit_count) 
VALUES ('free', 'gemini_analysis', 'daily', 10)
ON CONFLICT (plan_role, feature, period) 
DO UPDATE SET limit_count = EXCLUDED.limit_count;
```

### 3. Add a New Role
Roles are defined in `conthunt.users` via a CHECK constraint. To add a new plan (e.g., `enterprise`):

1.  **Update the Database Constraint**:
    ```sql
    ALTER TABLE conthunt.users 
    DROP CONSTRAINT users_role_check;
    
    ALTER TABLE conthunt.users 
    ADD CONSTRAINT users_role_check 
    CHECK (role IN ('free', 'creator', 'pro_research', 'enterprise'));
    ```

2.  **Add Limits for the New Role**:
    ```sql
    -- Enterprise: 10,000 per month, also 500 per hour to prevent spikes
    INSERT INTO plan_limits (plan_role, feature, period, limit_count) VALUES
    ('enterprise', 'gemini_analysis', 'monthly', 10000),
    ('enterprise', 'gemini_analysis', 'hourly', 500);
    ```

### 4. Remove a Limit
To remove a restriction (e.g., remove the hourly limit for Creators):
```sql
DELETE FROM plan_limits 
WHERE plan_role = 'creator' AND feature = 'gemini_analysis' AND period = 'hourly';
```

## Supported Periods
The `period` column supports the following values:
*   `hourly`: Resets at the top of every hour (XX:00:00).
*   `daily`: Resets at midnight UTC (00:00:00).
*   `monthly`: Resets on the 1st of every month.
*   `yearly`: Resets on Jan 1st of every year.
*   `total`: Never resets (lifetime limit).

## Usage Tracking Logic
*   **Timezone**: All periods are calculated in **UTC**.
*   **Overage**: If a user is downgraded (e.g., Pro -> Free), their existing usage for the period counts against the new lower limit immediately.
*   **Fail Safe**: If a user has NO row in `plan_limits` for a feature, they are allowed **unlimited** usage (or blocked, depending on application code default - currently defaults to ALLOW if no rows exist).

## adding new features
To start tracking a new feature (e.g., `video_export`):
1.  Add code to call `usage_tracker.record_usage(..., feature='video_export')`.
2.  Add limits in SQL:
    ```sql
    INSERT INTO plan_limits (plan_role, feature, period, limit_count) VALUES
    ('free', 'video_export', 'total', 5),      -- Free users: 5 lifetime exports
    ('creator', 'video_export', 'daily', 10);  -- Creators: 10 per day
    ```
