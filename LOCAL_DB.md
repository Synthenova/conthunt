# Local Postgres + PgBouncer (No Cloud SQL Proxy)

This repo can run fully local Postgres and PgBouncer via Docker Compose to avoid the Cloud SQL Proxy latency.

## Start DB + PgBouncer

```bash
docker compose -f docker-compose.db.yml up -d
docker compose -f docker-compose.db.yml ps
```

Helper scripts:
```bash
./scripts/dev_db_up.sh     # start
./scripts/dev_db_down.sh   # stop
./scripts/dev_db_reset.sh  # stop + delete local volume + start fresh (DANGEROUS)
```

Recommended order for a fresh local environment:
```bash
./scripts/dev_db_reset.sh
```

Note: run Alembic migrations directly against Postgres (port 5432). Use PgBouncer (port 6432) for the app.

Ports:
- Postgres: `localhost:5432`
- PgBouncer: `localhost:6432` (use this from the backend)

Note: This runs Postgres and PgBouncer as separate containers. It still shares the same laptop/network namespace, so you will not see the real Cloud SQL + VM network latency. The main win is removing the Cloud SQL Proxy from your dev loop while still keeping connection pooling behavior (PgBouncer) and coarse connection limits.

Default credentials (from `docker-compose.db.yml`):
- User: `conthunt_service`
- Password: `conthunt_local`
- Database: `postgres`
- Schema: `conthunt`

## Backend Env

Set `backend/.env.local` (or export env vars) to point at PgBouncer:

```bash
DATABASE_URL=postgresql+asyncpg://conthunt_service:conthunt_local@127.0.0.1:6432/postgres
DB_SCHEMA=conthunt
DB_PGBOUNCER_MODE=transaction
DB_USE_NULLPOOL=true
DB_SEMAPHORE_ENABLED=true
DB_SEM_API_LIMIT=7
DB_SEM_TASKS_LIMIT=13
DB_SEM_API_MAX_WAIT_MS=5000
DB_SEM_TASKS_MAX_WAIT_MS=20000
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=10
```

## Alembic Migrations

Alembic lives in `backend/alembic/`.

Baseline strategy:
- Local dev bootstraps the schema by applying the legacy SQL migrations in `backend/.sqls` (via `scripts/dev_db_apply_sqls.sh`, called by `scripts/dev_db_reset.sh`).
- Then we `alembic stamp head` to mark the current schema as the baseline revision (`0001_initial`).
- All future schema changes must be made as new Alembic revisions after `0001_initial`.

### Existing DB (already has tables)

If you restored from a snapshot or already bootstrapped via `backend/.sqls`, mark the baseline as applied:

```bash
cd backend
alembic stamp head
```

After stamping, future migrations work normally:

```bash
cd backend
alembic upgrade head
```

Create a new migration (SQL-first):

```bash
cd backend
alembic revision -m "your change"
```

Then edit the generated revision under `backend/alembic/versions/` and use `op.execute(...)`.

## Syncing Cloud SQL

Treat Alembic as the source of truth:
- Baseline is `0001_initial` (no-op) stamped onto the existing schema.
- New schema changes are added only as new revisions in `backend/alembic/versions/`.

### Cloud SQL Is Fresh (empty DB)

If Cloud SQL is empty, you need to bootstrap the schema there (for now, the same way as local):
- apply the legacy SQL migrations (`backend/.sqls`) or restore from a snapshot
- then stamp Alembic to the baseline

### Cloud SQL Already Has The Baseline Schema

If Cloud SQL already has the schema (same as your baseline), do NOT replay the baseline. Instead:
```bash
cd backend
export DATABASE_URL='<cloud-sql-url>'
export DB_SCHEMA=conthunt
alembic stamp head
```

After stamping, future changes are applied normally:
```bash
cd backend
alembic upgrade head
```

### Add New Schema Change Locally And Sync

```bash
cd backend
alembic revision -m "describe change"
# edit the revision file under backend/alembic/versions/
alembic upgrade head                 # apply locally

export DATABASE_URL='<cloud-sql-url>'
alembic upgrade head                 # apply to Cloud SQL
```

## "Realistic Enough" Constraints

Tune these in `docker-compose.db.yml` / `pgbouncer/pgbouncer.docker.ini`:
- Postgres `max_connections` (currently `200`)
- PgBouncer `max_client_conn`, `default_pool_size`, `pool_mode`
- Docker CPU/RAM caps (`cpus`, `mem_limit`) for `postgres` and `pgbouncer`



---

To “sync” from now on, you want **one baseline revision**, then only **incremental Alembic revisions** applied to both local and Cloud SQL.

### One-time setup (pick the correct case)

#### Case A: Cloud SQL is empty (fresh instance)
1. Point Alembic at Cloud SQL and run:
```bash
cd backend
export DATABASE_URL='<cloud-sql-url>'
export DB_SCHEMA=conthunt
APP_ENV=local alembic upgrade head
```
This will apply any Alembic revisions after the baseline (but it will not create the baseline schema for you).

#### Case B: Cloud SQL already has the schema that matches your baseline
1. Do **not** run `upgrade head` first. Instead “mark baseline as applied”:
```bash
cd backend
export DATABASE_URL='<cloud-sql-url>'
export DB_SCHEMA=conthunt
APP_ENV=local alembic stamp head
```
2. Then apply any newer migrations (if you have them):
```bash
APP_ENV=local alembic upgrade head
```

That’s the sync. From this point on, Cloud SQL and local are in the same Alembic timeline.

---

### Day-to-day workflow (local change -> Cloud SQL)

1. Create a new migration:
```bash
cd backend
alembic revision -m "describe change"
```

2. Edit the new file under `backend/alembic/versions/` and add `op.execute(...)` statements.

3. Apply locally:
```bash
APP_ENV=local alembic upgrade head
```

4. Apply to Cloud SQL:
```bash
export DATABASE_URL='<cloud-sql-url>'
export DB_SCHEMA=conthunt
APP_ENV=local alembic upgrade head
```

---

### Rule that prevents drift
After you start doing new Alembic revisions, stop editing `backend/.sqls` as the source of truth. Treat it as historical bootstrap only, and put all new changes in Alembic revisions.

If you tell me how you connect to Cloud SQL for migrations (Cloud SQL Proxy locally vs CI job in GCP), I’ll give you the exact recommended command/env setup for that path.
