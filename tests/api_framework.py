import argparse
import asyncio
import json
import os
import uuid
import logging
from typing import Any, Dict, Iterable, List, Optional, Set

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "https://conthunt-976912795426.us-central1.run.app")
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjA4MmU5NzVlMDdkZmE0OTYwYzdiN2I0ZmMxZDEwZjkxNmRjMmY1NWIiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiTmlybWFsIFYiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSTRJVmU5aFJSRFJmeGdhcW1MbmtoRzVSUTZ4ZGoydnZsR2tnX01WMGNpOTUwd29RPXM5Ni1jIiwiZGJfdXNlcl9pZCI6IjY4ZGE1YzI3LWZmYzItNDE4Zi05YTJiLTUwYjdkNjg2YzczZCIsInJvbGUiOiJjcmVhdG9yIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2NvbnRodW50LWRldiIsImF1ZCI6ImNvbnRodW50LWRldiIsImF1dGhfdGltZSI6MTc2ODcyMjczNywidXNlcl9pZCI6ImhaVFBUQVNXQnVnTnlhdmc0QUxrdzNCcVFmdzEiLCJzdWIiOiJoWlRQVEFTV0J1Z055YXZnNEFMa3czQnFRZncxIiwiaWF0IjoxNzY4NzU2MzQ3LCJleHAiOjE3Njg3NTk5NDcsImVtYWlsIjoibGFtcmluQHN5bnRoZW5vdmEueHl6IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDUyMTc2ODYyNTU3MzIzNDc2MjYiXSwiZW1haWwiOlsibGFtcmluQHN5bnRoZW5vdmEueHl6Il19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.qdsQD94OlaNyoMkoESkozdomSvXWqnEfg0uMh2hUUT9-aIgfn5EbCzzbokO2HkxfXtiuNtEXklsTWSQB7GS8QrDqXv9hgiJzw2REdliGHQ9FvsZSloCxCoJaHxFoVRwFmo4ilMVHw2IdINIK6f5sJZMH6g2mxRsrhNhoFNyZ02lDdhQCV3fVa4CldWVbKk6s9_v1PAsVgrejmsbH4Kea7UwW0UzlGM5fZwb1mBlv1EQzlrcOKhZzuJl5x5KHqZ-G6q7HR7rhYpxcKBHRLJTvuVgx4Ft_0xgI-yaVo-psE3ycc1SkMvPn1AC9V5ACbc1MqECsZjaDVZOjSQRHSU5I-Q"

MODEL_NAME = "google/gemini-3-flash-preview"
MESSAGE_1 = os.getenv("MESSAGE_1", "Find me trending fitness content")
MESSAGE_2 = os.getenv("MESSAGE_2", "retreive one search and analyse top 10 videos")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api-framework")


def build_headers() -> Dict[str, str]:
    if not BEARER_TOKEN:
        raise SystemExit("BEARER_TOKEN is empty. Fill it in before running.")
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }


async def parse_sse_events(response: httpx.Response) -> Iterable[str]:
    data_lines: List[str] = []
    async for line in response.aiter_lines():
        if line is None:
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
            continue
        if line == "":
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
            continue

    if data_lines:
        yield "\n".join(data_lines)


async def create_chat(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    flow_id: int,
) -> Dict[str, Any]:
    payload = {
        "title": "New Chat",
        "context_type": None,
        "context_id": None,
    }
    logger.info("[flow-%s] Creating chat...", flow_id)
    resp = await client.post(f"{BACKEND_URL}/v1/chats", headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    logger.info("[flow-%s] Chat created: %s", flow_id, data.get("id"))
    return data


async def send_message(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    chat_id: str,
    message: str,
    flow_id: int,
) -> None:
    client_id = str(uuid.uuid4())
    payload = {
        "message": message,
        "client_id": client_id,
        "model": MODEL_NAME,
    }
    logger.info("[flow-%s] Sending message: %s", flow_id, message)
    resp = await client.post(
        f"{BACKEND_URL}/v1/chats/{chat_id}/send",
        headers=headers,
        json=payload,
    )
    resp.raise_for_status()
    logger.info("[flow-%s] Message accepted (client_id=%s).", flow_id, client_id)


async def stream_chat(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    chat_id: str,
    flow_id: int,
) -> None:
    url = f"{BACKEND_URL}/v1/chats/{chat_id}/stream"
    logger.info("[flow-%s] Streaming chat response...", flow_id)
    async with client.stream("GET", url, headers=headers) as resp:
        resp.raise_for_status()
        async for data in parse_sse_events(resp):
            if not data:
                continue
            payload = json.loads(data)
            if payload.get("type") == "done":
                logger.info("[flow-%s] Chat stream done.", flow_id)
                return
            if payload.get("type") == "error":
                raise RuntimeError(payload.get("error") or "Chat stream error")


async def fetch_chat_tags(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    chat_id: str,
) -> List[Dict[str, Any]]:
    resp = await client.get(f"{BACKEND_URL}/v1/chats/{chat_id}/tags", headers=headers)
    resp.raise_for_status()
    return resp.json()


async def get_search_detail(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    search_id: str,
) -> Dict[str, Any]:
    resp = await client.get(f"{BACKEND_URL}/v1/searches/{search_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()


async def stream_search(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    search_id: str,
    flow_id: int,
) -> None:
    url = f"{BACKEND_URL}/v1/search/{search_id}/stream"
    logger.info("[flow-%s] Streaming search %s...", flow_id, search_id)
    async with client.stream("GET", url, headers=headers) as resp:
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await resp.json()
            status = data.get("status")
            if status == "failed":
                raise RuntimeError(data.get("error") or "Search failed")
            logger.info("[flow-%s] Search %s already completed.", flow_id, search_id)
            return

        async for data in parse_sse_events(resp):
            if not data:
                continue
            payload = json.loads(data)
            if payload.get("type") == "done":
                logger.info("[flow-%s] Search %s stream done.", flow_id, search_id)
                return
            if payload.get("type") == "error":
                raise RuntimeError(payload.get("error") or "Search stream error")


async def stream_search_flow(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    search_id: str,
    flow_id: int,
) -> None:
    logger.info("[flow-%s] Starting search flow for %s", flow_id, search_id)
    detail = await get_search_detail(client, headers, search_id)
    status = detail.get("status")
    if status == "completed":
        logger.info("[flow-%s] Search %s already completed.", flow_id, search_id)
        return
    if status == "failed":
        raise RuntimeError("Search failed")

    await stream_search(client, headers, search_id, flow_id)
    await get_search_detail(client, headers, search_id)
    logger.info("[flow-%s] Search %s detail refreshed.", flow_id, search_id)


async def poll_chat_search_tags(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    chat_id: str,
    seen_search_ids: Set[str],
    search_tasks: Dict[str, asyncio.Task],
    stop_event: asyncio.Event,
    flow_id: int,
) -> None:
    while not stop_event.is_set():
        tags = await fetch_chat_tags(client, headers, chat_id)
        for tag in tags:
            if tag.get("type") != "search":
                continue
            search_id = str(tag.get("id"))
            if not search_id or search_id in seen_search_ids:
                continue
            seen_search_ids.add(search_id)
            logger.info("[flow-%s] Discovered search tag: %s", flow_id, search_id)
            search_tasks[search_id] = asyncio.create_task(
                stream_search_flow(client, headers, search_id, flow_id)
            )
        await asyncio.sleep(2)


async def run_flow(client: httpx.AsyncClient, headers: Dict[str, str], flow_id: int) -> None:
    chat = await create_chat(client, headers, flow_id)
    chat_id = str(chat["id"])

    seen_search_ids: Set[str] = set()
    search_tasks: Dict[str, asyncio.Task] = {}
    stop_event = asyncio.Event()

    tag_task = asyncio.create_task(
        poll_chat_search_tags(
            client,
            headers,
            chat_id,
            seen_search_ids,
            search_tasks,
            stop_event,
            flow_id,
        )
    )

    logger.info("[flow-%s] Starting first send/stream cycle...", flow_id)
    await send_message(client, headers, chat_id, MESSAGE_1, flow_id)
    await stream_chat(client, headers, chat_id, flow_id)

    logger.info("[flow-%s] Starting second send/stream cycle...", flow_id)
    await send_message(client, headers, chat_id, MESSAGE_2, flow_id)
    await stream_chat(client, headers, chat_id, flow_id)

    stop_event.set()
    await tag_task

    if search_tasks:
        await asyncio.gather(*search_tasks.values())
    logger.info("[flow-%s] All done.", flow_id)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flows", type=int, default=1)
    args = parser.parse_args()

    headers = build_headers()
    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = [run_flow(client, headers, i) for i in range(args.flows)]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
