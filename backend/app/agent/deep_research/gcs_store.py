from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from google.cloud import storage

from app.core import get_settings

settings = get_settings()

_CLIENT: storage.Client | None = None


def get_gcs_client() -> storage.Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = storage.Client()
    return _CLIENT


def _root_prefix(chat_id: str) -> str:
    return f"deepagents/{chat_id}/"


def _key(chat_id: str, path: str) -> str:
    path = path.lstrip("/")
    return f"{_root_prefix(chat_id)}{path}"


async def blob_exists(chat_id: str, path: str) -> bool:
    key = _key(chat_id, path)

    def _exists() -> bool:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        return blob.exists()

    return await asyncio.to_thread(_exists)


async def read_json(chat_id: str, path: str) -> Optional[dict]:
    key = _key(chat_id, path)

    def _read() -> Optional[dict]:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        if not blob.exists():
            return None
        content = blob.download_as_text()
        return json.loads(content)

    return await asyncio.to_thread(_read)


async def write_json(chat_id: str, path: str, payload: dict) -> None:
    key = _key(chat_id, path)
    data = json.dumps(payload, ensure_ascii=False, indent=2)

    def _write() -> None:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        blob.upload_from_string(data.encode("utf-8"), content_type="application/json")

    await asyncio.to_thread(_write)


async def read_text(chat_id: str, path: str) -> str:
    key = _key(chat_id, path)

    def _read() -> str:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        if not blob.exists():
            return ""
        return blob.download_as_text()

    return await asyncio.to_thread(_read)


async def write_text(chat_id: str, path: str, content: str, *, content_type: str = "text/plain") -> None:
    key = _key(chat_id, path)

    def _write() -> None:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        blob.upload_from_string(content.encode("utf-8"), content_type=content_type)

    await asyncio.to_thread(_write)


async def list_paths(chat_id: str, prefix: str) -> list[str]:
    """
    List relative paths under the chat root that start with prefix.
    Example: prefix="mycrit-" returns ["mycrit-001.json", "mycrit-002.json", ...]
    """
    prefix = prefix.lstrip("/")
    key_prefix = _key(chat_id, prefix)
    root = _root_prefix(chat_id)

    def _list() -> list[str]:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        out: list[str] = []
        for blob in client.list_blobs(bucket, prefix=key_prefix):
            name = blob.name
            if not name.startswith(root):
                continue
            rel = name[len(root):]
            out.append(rel)
        return out

    return await asyncio.to_thread(_list)


async def append_jsonl(chat_id: str, path: str, record: dict) -> None:
    """
    Append a JSON record as a new line to a .jsonl file in GCS.
    Uses read-modify-write (not atomic in GCS, but sufficient for per-chat audit logs).
    """
    existing = await read_text(chat_id, path)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    needs_nl = bool(existing) and (not existing.endswith("\n"))
    prefix = "\n" if needs_nl else ""
    content = f"{existing}{prefix}{line}\n"
    await write_text(chat_id, path, content, content_type="application/x-ndjson")

