"""
One-time script to backfill chat_tags from existing chat message history.

Scans each chat's checkpointed messages for chip fences and search tool outputs,
derives board/search/media tags, and upserts them into conthunt.chat_tags with
newest-first sort_order. Agent-originated search tool outputs are marked source=agent.

Usage:
    python backend/scripts/backfill_chat_tags.py

Requires DATABASE_URL and auth to access the DB. Does not modify messages.
"""
import asyncio
import json
import re
from urllib.parse import quote

from sqlalchemy import text
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core import get_settings, logger
from app.db import get_db_connection, set_rls_user, queries

CHIP_FENCE_RE = re.compile(r"```chip\s+([\s\S]*?)```", re.MULTILINE)


def _parse_chip_block(raw: str):
    """Parse a single chip fence payload into (type, id, label)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    # JSON form {"type": "...", "id": "...", "label": "..."}
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("type") and data.get("id"):
                return data.get("type"), data.get("id"), data.get("label")
        except Exception:
            return None
    # Legacy form e.g. "board::123" or "search::abc"
    if "::" in raw:
        parts = raw.split("::", 1)
        if len(parts) == 2:
            return parts[0], parts[1], None
    return None


def extract_tags_from_messages(messages):
    """
    Extract tags from a list of LangGraph messages.
    Returns a list of tag dicts with type, tag_id, label, source, sort_order.
    Newest messages produce the smallest sort_order (top-first).
    """
    seen = set()
    tags = []
    sort_cursor = -1

    for msg in messages or []:
        m_type = getattr(msg, "type", None) if not isinstance(msg, dict) else msg.get("type")
        content = getattr(msg, "content", "") if not isinstance(msg, dict) else msg.get("content", "")

        # 1) Chip fences in any message content
        if isinstance(content, str):
            for match in CHIP_FENCE_RE.finditer(content):
                parsed = _parse_chip_block(match.group(1))
                if not parsed:
                    continue
                c_type, c_id, c_label = parsed
                key = (c_type, c_id)
                if key in seen:
                    continue
                seen.add(key)
                tags.append({
                    "type": c_type,
                    "tag_id": c_id,
                    "label": c_label,
                    "source": "user",
                    "sort_order": sort_cursor,
                })
                sort_cursor -= 1

        # 2) Tool outputs with search_ids
        if m_type == "tool":
            raw_str = content
            if not isinstance(raw_str, str):
                try:
                    raw_str = json.dumps(raw_str)
                except Exception:
                    raw_str = ""
            parsed_data = None
            try:
                parsed_data = json.loads(raw_str)
            except Exception:
                try:
                    # Handle double-encoded
                    inner = json.loads(raw_str)
                    if isinstance(inner, str):
                        parsed_data = json.loads(inner)
                    else:
                        parsed_data = inner
                except Exception:
                    parsed_data = None

            if parsed_data and isinstance(parsed_data, dict):
                search_ids = parsed_data.get("search_ids") or []
                for s in search_ids:
                    search_id = s.get("search_id") or s.get("id")
                    if not search_id:
                        continue
                    label = s.get("keyword") or s.get("label") or search_id
                    key = ("search", search_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    tags.append({
                        "type": "search",
                        "tag_id": search_id,
                        "label": label,
                        "source": "agent",
                        "sort_order": sort_cursor,
                    })
                    sort_cursor -= 1

    return tags


async def filter_existing_searches(conn, tags):
    """Keep only search tags whose IDs exist in conthunt.searches."""
    search_ids = [t["tag_id"] for t in tags if t.get("type") == "search"]
    if not search_ids:
        return tags

    rows = await conn.execute(
        text("SELECT id FROM conthunt.searches WHERE id = ANY(:ids)"),
        {"ids": search_ids}
    )
    valid_ids = {r[0] for r in rows}
    filtered = []
    skipped = 0
    for t in tags:
        if t.get("type") == "search":
            if t["tag_id"] in valid_ids:
                filtered.append(t)
            else:
                skipped += 1
        else:
            filtered.append(t)
    if skipped:
        logger.info(f"[backfill] skipped {skipped} search tags with missing searches")
    return filtered


async def build_saver():
    """Build AsyncPostgresSaver with proper search_path and keepalives."""
    settings = get_settings()
    pg_url = settings.DATABASE_URL
    if pg_url.startswith("postgresql+psycopg://"):
        pg_url = pg_url.replace("postgresql+psycopg://", "postgresql://")
    elif pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql+asyncpg://", "postgresql://")

    schema = settings.DB_SCHEMA
    options_param = quote(f"-c search_path={schema},public")
    keepalive_params = "keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"
    if "?" in pg_url:
        pg_url = f"{pg_url}&options={options_param}"
    else:
        pg_url = f"{pg_url}?options={options_param}"
    pg_url = f"{pg_url}&{keepalive_params}"

    saver_cm = AsyncPostgresSaver.from_conn_string(pg_url)
    saver = await saver_cm.__aenter__()
    await saver.setup()
    return saver_cm, saver


def extract_messages_from_checkpoint(checkpoint_obj):
    """Handle various checkpoint shapes to extract messages list."""
    if not checkpoint_obj:
        return []
    candidates = []
    if isinstance(checkpoint_obj, dict):
        candidates.append(checkpoint_obj)
        if "values" in checkpoint_obj and isinstance(checkpoint_obj["values"], dict):
            candidates.append(checkpoint_obj["values"])
        if "state" in checkpoint_obj and isinstance(checkpoint_obj["state"], dict):
            candidates.append(checkpoint_obj["state"])
        if "v" in checkpoint_obj and isinstance(checkpoint_obj["v"], dict):
            candidates.append(checkpoint_obj["v"])
        # Search nested dicts for messages key
        for val in checkpoint_obj.values():
            if isinstance(val, dict) and "messages" in val:
                candidates.append(val)
    for cand in candidates:
        if isinstance(cand, dict) and "messages" in cand:
            return cand.get("messages") or []
    return []


async def main():
    settings = get_settings()
    saver_cm, saver = await build_saver()
    total_tags = 0
    total_chats = 0
    chat_count = 0

    try:
        async with get_db_connection() as conn:
            # Temporarily disable RLS for bulk backfill; re-enable afterwards
            await conn.execute(text("SET row_security = off"))
            # Start fresh as requested
            logger.info("[backfill] truncating chat_tags before re-fill")
            await conn.execute(text("TRUNCATE conthunt.chat_tags"))
            await conn.commit()

            rows = await conn.execute(text("""
                SELECT id, user_id, thread_id, title
                FROM conthunt.chats
                WHERE deleted_at IS NULL
            """))
            chats = rows.fetchall()
            chat_count = len(chats)

            for idx, (chat_id, user_id, thread_id, title) in enumerate(chats, start=1):
                total_chats += 1
                try:
                    checkpoint = await saver.aget({"configurable": {"thread_id": thread_id}})
                    # Normalize checkpoint into a dict
                    cp_dict = None
                    if isinstance(checkpoint, dict):
                        cp_dict = checkpoint.get("checkpoint") or checkpoint
                    elif hasattr(checkpoint, "checkpoint"):
                        cp_dict = checkpoint.checkpoint
                    if not cp_dict:
                        if idx % 25 == 0:
                            logger.info(f"[backfill] progress {idx}/{chat_count}: no checkpoint for chat {chat_id}")
                        continue
                    messages = extract_messages_from_checkpoint(cp_dict)
                    tags = extract_tags_from_messages(messages)
                    before_filter = len([t for t in tags if t.get("type") == "search"])
                    tags = await filter_existing_searches(conn, tags)
                    after_filter = len([t for t in tags if t.get("type") == "search"])
                    if before_filter and before_filter != after_filter:
                        logger.info(f"[backfill] chat={chat_id} filtered {before_filter - after_filter} missing searches (kept {after_filter})")
                    if not tags:
                        if idx % 25 == 0:
                            logger.info(f"[backfill] progress {idx}/{chat_count}: no tags for chat {chat_id}")
                        continue
                    await set_rls_user(conn, user_id)
                    await queries.upsert_chat_tags(conn, chat_id, tags)
                    await conn.commit()
                    total_tags += len(tags)
                    logger.info(f"[backfill] ({idx}/{chat_count}) chat={chat_id} title={title!r}: added {len(tags)} tags")
                except Exception as e:
                    logger.error(f"[backfill] failed chat={chat_id}: {e}", exc_info=True)
                    try:
                        await conn.rollback()
                    except Exception:
                        pass
    finally:
        try:
            async with get_db_connection() as conn:
                await conn.execute(text("SET row_security = on"))
        except Exception:
            logger.warning("Failed to re-enable row_security; please verify manually.")
        finally:
            try:
                await saver_cm.__aexit__(None, None, None)
            except Exception:
                pass

    logger.info(f"[backfill] completed: chats scanned={total_chats} tags upserted={total_tags}")


if __name__ == "__main__":
    asyncio.run(main())
