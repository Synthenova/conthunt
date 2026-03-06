"""Initial Alembic revision (full schema baseline).

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-09

This revision creates the full `conthunt` schema from an empty database using
the canonical schema snapshot SQL. Existing environments can be stamped to this
revision and then upgraded normally.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _iter_sql_statements(sql_text: str) -> list[str]:
    filtered_lines: list[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped:
            filtered_lines.append("")
            continue
        if stripped.startswith("--"):
            continue
        if stripped.startswith("\\"):
            continue
        filtered_lines.append(line)

    sql_text = "\n".join(filtered_lines)

    # Split SQL script into executable statements while respecting quoted strings.
    statements: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False

    i = 0
    n = len(sql_text)
    while i < n:
        ch = sql_text[i]

        if ch == "'" and not in_double:
            if in_single and i + 1 < n and sql_text[i + 1] == "'":
                buf.append(ch)
                buf.append(sql_text[i + 1])
                i += 2
                continue
            in_single = not in_single
            buf.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            i += 1
            continue

        if ch == ";" and not in_single and not in_double:
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "0001_full_schema_baseline.sql"
    sql_text = sql_path.read_text()

    bind = op.get_bind()
    for statement in _iter_sql_statements(sql_text):
        bind.exec_driver_sql(statement)


def downgrade() -> None:
    raise NotImplementedError("Downgrades are not supported.")
