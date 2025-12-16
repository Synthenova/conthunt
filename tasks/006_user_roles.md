# User Role-Based Authentication

**Date:** 2025-12-15

## Overview

Implemented role-based access control (RBAC) with three subscription tiers: `free`, `creator`, and `pro_research`. Roles are stored in the database and embedded in JWT custom claims for efficient access control.

---

## Completed Work

### 1. Database Schema

- **Migration:** `005_user_roles.sql`
  - Added `role` column to `users` table with CHECK constraint
  - Default role: `free`
  - Index on `role` column for efficient queries

### 2. Schemas & Models

- **`app/schemas/roles.py`**
  - `UserRole` enum (free, creator, pro_research)
  - `UserRoleUpdate` — webhook request body
  - `UserInfo` — user info with role

### 3. Database Queries

- **`app/db/queries/users.py`**
  - `get_user_role(user_id)` — fetch current role
  - `update_user_role(firebase_uid, new_role)` — update role by UID

- **Updated `app/db/users.py`**
  - `get_or_create_user()` now returns `(user_id, role)` tuple

### 4. Authentication Module

- **`app/auth/firebase.py`**
  - Added `AuthUser` TypedDict with `uid`, `email`, `role`
  - `get_current_user()` extracts role from Firebase custom claims
  - Defaults to `free` if claim not present

- **`app/auth/dependencies.py`** (NEW)
  - `require_role(*roles)` — dependency factory for role checks
  - `require_creator` — allows creator or pro_research
  - `require_pro` — allows only pro_research

### 5. Webhook Endpoint

- **`app/api/v1/webhooks.py`** (NEW)
  - `POST /v1/webhooks/dodo/subscription`
  - Updates user role in DB
  - Syncs to Firebase custom claims
  - Placeholder signature verification (ready for Dodo integration)

### 6. Settings

- **`app/core/settings.py`**
  - Added `DODO_WEBHOOK_SECRET` for webhook authentication

### 7. Updated API Endpoints

All endpoints updated to handle new `get_or_create_user()` signature:
- `search.py`
- `history.py`
- `media.py`
- `boards.py`

---

## Usage Examples

### Protect an Endpoint

```python
from app.auth import require_pro, AuthUser
from fastapi import Depends

@router.get("/analytics")
async def analytics(user: AuthUser = Depends(require_pro)):
    return {"data": "pro-only analytics"}
```

### Update Role via Webhook

```bash
curl -X POST http://localhost:8000/v1/webhooks/dodo/subscription \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_uid": "abc123",
    "new_role": "creator"
  }'
```

---

## Migration Instructions

```bash
# Connect to Cloud SQL
psql -h localhost -p 5433 -U conthunt_app -d conthunt

# Run migration
\i backend/.sqls/005_user_roles.sql

# Verify
\d conthunt.users
```

---

## Dodo Integration (Future)

When integrating Dodo payments:

1. Set `DODO_WEBHOOK_SECRET` in production `.env`
2. Update `verify_dodo_signature()` with actual Dodo signature format
3. Map Dodo subscription plans to role values
4. Configure Dodo webhook URL: `https://your-domain.com/v1/webhooks/dodo/subscription`

---

## Files Created/Modified

```
backend/
├── .sqls/
│   └── 005_user_roles.sql (NEW)
├── app/
│   ├── schemas/
│   │   └── roles.py (NEW)
│   ├── db/
│   │   ├── users.py (MODIFIED)
│   │   └── queries/
│   │       └── users.py (NEW)
│   ├── auth/
│   │   ├── firebase.py (MODIFIED)
│   │   └── dependencies.py (NEW)
│   ├── api/v1/
│   │   ├── webhooks.py (NEW)
│   │   ├── router.py (MODIFIED)
│   │   ├── search.py (MODIFIED)
│   │   ├── history.py (MODIFIED)
│   │   ├── media.py (MODIFIED)
│   │   └── boards.py (MODIFIED)
│   └── core/
│       └── settings.py (MODIFIED)
```
