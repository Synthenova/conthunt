from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Alembic Config object, provides access to values in alembic.ini
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load backend env files for local runs (Alembic doesn't go through app Settings()).
# Environment variables still win; we do not override existing values.
_here = Path(__file__).resolve()
_backend_dir = _here.parents[1]  # backend/
_app_env = os.getenv("APP_ENV", "local")
load_dotenv(_backend_dir / ".env", override=False)
load_dotenv(_backend_dir / f".env.{_app_env}", override=False)

# This project uses SQL-first migrations (no SQLAlchemy model metadata).
target_metadata = None


def _to_sync_url(url: str) -> str:
    # Backend runtime uses asyncpg, but Alembic runs sync migrations.
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _get_db_url() -> str:
    url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if not url:
        raise RuntimeError("Missing DATABASE_URL (or ALEMBIC_DATABASE_URL) for Alembic.")
    return _to_sync_url(url)


def run_migrations_offline() -> None:
    url = _get_db_url()
    schema = os.getenv("DB_SCHEMA", "conthunt")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _get_db_url()
    schema = os.getenv("DB_SCHEMA", "conthunt")

    connectable = create_engine(url, poolclass=NullPool)

    with connectable.connect() as connection:
        # Match app behavior: all queries assume `conthunt` schema is on the search_path.
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
        connection.execute(text(f"SET search_path TO {schema}, public;"))
        # Ensure the version table exists. Alembic normally creates it, but we've observed
        # stamp/upgrade runs that log success without persisting the version row.
        connection.execute(
            text(
                f"CREATE TABLE IF NOT EXISTS {schema}.alembic_version "
                "(version_num VARCHAR(32) PRIMARY KEY);"
            )
        )
        # SQLAlchemy 2.0 connections are in "autobegin" mode; without an explicit commit
        # these DDL statements can be rolled back when the connection closes (e.g. on stamp).
        try:
            connection.commit()
        except Exception:
            # Some drivers/dialects may not support explicit commit here; ignore.
            pass

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
