import asyncio
import base64
import json
import time
from typing import Any, TypeVar
from uuid import UUID

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.agent.runtime import create_agent_graph
from app.api.v1.analysis import _execute_gemini_analysis
from app.api.v1.chats import stream_generator_to_redis
from app.api.v1.search import load_more_worker, search_worker
from app.core import get_settings, logger
from app.core.redis_client import get_app_redis
from app.core.telemetry_context import bind_telemetry, merge_telemetry, telemetry_from_mapping
from app.db.queries import update_board_insights_status, update_twelvelabs_asset_status
from app.db.queries.analysis import (
    update_analysis_status,
    update_analysis_status_completed_batch,
    update_analysis_status_failed_batch,
    update_analysis_status_processing_batch,
    update_analysis_status_queued_batch,
)
from app.db.queries.content import get_media_asset_by_id, get_media_assets_by_ids
from app.db.session import get_db_connection
from app.media.downloader import (
    claim_assets_for_download_batch,
    download_claimed_asset,
    reset_assets_pending_batch,
    update_assets_failed_batch,
    update_assets_stored_batch,
)
from app.services.board_insights import execute_board_insights
from app.services.cloud_tasks import cloud_tasks
from app.services.task_executor import CloudTaskExecutor
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.llm.global_rate_limiter import LlmRateLimited
from app.integrations.posthog_client import capture_event, capture_event_with_error, categorize_error

router = APIRouter()
settings = get_settings()

TPayload = TypeVar("TPayload", bound=BaseModel)


def _get_request_redis(request: Request) -> redis.Redis:
    return get_app_redis(request)


def _normalize_payload(payload_or_list: TPayload | list[TPayload]) -> tuple[list[TPayload], bool]:
    if isinstance(payload_or_list, list):
        return payload_or_list, False
    return [payload_or_list], True


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return False
    return True


def _is_llm_429_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, LlmRateLimited):
        return exc.kind in {"rpd", "rpm", "tpm"}
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return int(exc.response.status_code) == 429
        except Exception:
            return False
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        try:
            return int(status_code) == 429
        except Exception:
            return False
    response = getattr(exc, "response", None)
    if response is not None:
        response_status_code = getattr(response, "status_code", None)
        if response_status_code is not None:
            try:
                return int(response_status_code) == 429
            except Exception:
                return False
    return False


def _batch_summary(
    *,
    route: str,
    processed: int,
    succeeded: int,
    failed: int,
    retried_enqueued: int = 0,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "route": route,
        "batch": True,
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "retried_enqueued": retried_enqueued,
    }


class AnalysisTaskPayload(BaseModel):
    analysis_id: UUID
    media_asset_id: UUID
    video_uri: str
    chat_id: UUID | None = None
    user_id: UUID | None = None
    dispatched_at: float | None = None
    attempt_no: int = 0


class TwelveLabsTaskPayload(BaseModel):
    media_asset_id: UUID


class MediaDownloadTaskPayload(BaseModel):
    asset_id: UUID
    platform: str
    external_id: str
    priority: bool = False
    attempt_no: int = 0
    dispatched_at: float | None = None


class RawArchiveTaskPayload(BaseModel):
    platform: str
    search_id: UUID
    raw_json_compressed: str | None = None
    raw_json: dict | None = None
    gcs_key: str | None = None


class BoardInsightsTaskPayload(BaseModel):
    board_id: UUID
    user_id: UUID
    user_role: str


class SearchTaskPayload(BaseModel):
    search_id: UUID
    user_uuid: UUID
    query: str
    inputs: dict
    dispatched_at: float | None = None


class LoadMoreTaskPayload(BaseModel):
    search_id: UUID
    user_uuid: UUID
    query: str
    platform_cursors: dict


class ChatStreamTaskPayload(BaseModel):
    chat_id: UUID
    thread_id: str
    inputs: dict
    model_name: str | None = None
    image_urls: list[str] | None = None
    auth_token: str | None = None
    filters: dict | None = None
    user_id: UUID | None = None
    action_id: str | None = None
    session_id: str | None = None
    attempt_no: int | None = None
    feature: str | None = None
    operation: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    message_client_id: str | None = None


async def _handle_gemini_analysis_single(payload: AnalysisTaskPayload, request: Request) -> dict[str, Any]:
    logger.info("Received Gemini analysis task for %s", payload.media_asset_id)
    executor = CloudTaskExecutor(request, retry_decider=_is_llm_429_retryable_exception)

    async def _on_fail(e: Exception):
        async with get_db_connection() as conn:
            await update_analysis_status(
                conn,
                analysis_id=payload.analysis_id,
                status="failed",
                error=str(e),
            )
            await conn.commit()

    async with get_db_connection() as conn:
        await update_analysis_status(conn, payload.analysis_id, status="processing")
        asset = await get_media_asset_by_id(conn, payload.media_asset_id)
        await conn.commit()

    if not asset:
        await _on_fail(Exception("Media asset not found"))
        return {"status": "failed", "error": "Media asset not found"}

    source_url = asset.get("source_url", "")
    is_youtube = "youtube.com" in source_url or "youtu.be" in source_url

    if not is_youtube:
        for attempt in range(18):
            async with get_db_connection() as conn:
                asset = await get_media_asset_by_id(conn, payload.media_asset_id)
                await conn.commit()
            status = asset.get("status", "") if asset else ""
            if status in ("stored", "downloaded"):
                break
            if status == "failed":
                await _on_fail(Exception("Video download failed"))
                return {"status": "failed", "error": "Video download failed"}
            logger.info(
                "Video not ready (status=%s), waiting... attempt %s/18 for %s",
                status,
                attempt + 1,
                payload.media_asset_id,
            )
            await asyncio.sleep(10)
        else:
            await _on_fail(Exception("Video not ready after 3 min timeout"))
            return {"status": "failed", "error": "Video not ready after timeout"}

    final_video_uri = payload.video_uri
    if asset:
        final_video_uri = asset.get("gcs_uri") or asset.get("video_url") or payload.video_uri

    return await executor.run(
        handler=_execute_gemini_analysis,
        on_fail=_on_fail,
        analysis_id=payload.analysis_id,
        media_asset_id=payload.media_asset_id,
        video_uri=final_video_uri,
        chat_id=str(payload.chat_id) if payload.chat_id else None,
        user_id=str(payload.user_id) if payload.user_id else None,
        dispatched_at=payload.dispatched_at,
        persist=True,
    )


async def _handle_gemini_analysis_batch(items: list[AnalysisTaskPayload]) -> dict[str, Any]:
    if not items:
        return _batch_summary(route="gemini/analyze", processed=0, succeeded=0, failed=0)

    deduped: dict[UUID, AnalysisTaskPayload] = {}
    for item in items:
        deduped[item.analysis_id] = item
    task_items = list(deduped.values())

    analysis_ids = [item.analysis_id for item in task_items]
    media_asset_ids = [item.media_asset_id for item in task_items]

    async with get_db_connection() as conn:
        await update_analysis_status_processing_batch(conn, analysis_ids)
        assets = await get_media_assets_by_ids(conn, media_asset_ids)
        await conn.commit()
    assets_by_id = {row["id"]: row for row in assets}

    ready_jobs: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    failed_events: list[dict[str, Any]] = []

    waiting_by_asset_id: dict[UUID, AnalysisTaskPayload] = {}
    for item in task_items:
        asset = assets_by_id.get(item.media_asset_id)
        if not asset:
            failed_rows.append({"analysis_id": item.analysis_id, "error": "Media asset not found"})
            failed_events.append({"payload": item, "error": "Media asset not found"})
            continue

        source_url = asset.get("source_url", "")
        is_youtube = "youtube.com" in source_url or "youtu.be" in source_url
        status = asset.get("status", "")

        if is_youtube:
            ready_jobs.append(
                {
                    "payload": item,
                    "video_uri": source_url or item.video_uri,
                }
            )
            continue

        if status in ("stored", "downloaded"):
            ready_jobs.append(
                {
                    "payload": item,
                    "video_uri": asset.get("gcs_uri") or asset.get("video_url") or item.video_uri,
                }
            )
            continue

        if status == "failed":
            failed_rows.append({"analysis_id": item.analysis_id, "error": "Video download failed"})
            failed_events.append({"payload": item, "error": "Video download failed"})
            continue

        waiting_by_asset_id[item.media_asset_id] = item

    for attempt in range(18):
        if not waiting_by_asset_id:
            break
        async with get_db_connection() as conn:
            polled_assets = await get_media_assets_by_ids(conn, list(waiting_by_asset_id.keys()))
            await conn.commit()
        polled_by_id = {row["id"]: row for row in polled_assets}
        done_ids: list[UUID] = []

        for media_asset_id, item in waiting_by_asset_id.items():
            asset = polled_by_id.get(media_asset_id)
            status = asset.get("status", "") if asset else ""
            if status in ("stored", "downloaded"):
                ready_jobs.append(
                    {
                        "payload": item,
                        "video_uri": (asset.get("gcs_uri") or asset.get("video_url") or item.video_uri),
                    }
                )
                done_ids.append(media_asset_id)
            elif status == "failed":
                failed_rows.append({"analysis_id": item.analysis_id, "error": "Video download failed"})
                failed_events.append({"payload": item, "error": "Video download failed"})
                done_ids.append(media_asset_id)

        for media_asset_id in done_ids:
            waiting_by_asset_id.pop(media_asset_id, None)

        if waiting_by_asset_id:
            await asyncio.sleep(10)

    for item in waiting_by_asset_id.values():
        failed_rows.append({"analysis_id": item.analysis_id, "error": "Video not ready after timeout"})
        failed_events.append({"payload": item, "error": "Video not ready after timeout"})

    success_rows: list[dict[str, Any]] = []
    success_events: list[AnalysisTaskPayload] = []
    runtime_failed_rows: list[dict[str, Any]] = []
    retry_analysis_ids: list[UUID] = []
    retry_payloads: list[dict[str, Any]] = []

    async def _process_ready(job: dict[str, Any]) -> None:
        payload: AnalysisTaskPayload = job["payload"]
        video_uri = job["video_uri"]
        try:
            result = await _execute_gemini_analysis(
                analysis_id=payload.analysis_id,
                media_asset_id=payload.media_asset_id,
                video_uri=video_uri,
                chat_id=str(payload.chat_id) if payload.chat_id else None,
                user_id=str(payload.user_id) if payload.user_id else None,
                dispatched_at=payload.dispatched_at,
                persist=False,
            )
            success_rows.append({"analysis_id": payload.analysis_id, "analysis": result.get("analysis", "")})
            success_events.append(payload)
        except Exception as exc:
            err_text = f"{exc} (URL: {video_uri})"
            attempt_no = int(payload.attempt_no or 0)
            if _is_llm_429_retryable_exception(exc) and (attempt_no + 1) < int(getattr(settings, "TASK_WORKER_MAX_ATTEMPTS", 5)):
                retry_analysis_ids.append(payload.analysis_id)
                retry_payloads.append(
                    {
                        "analysis_id": str(payload.analysis_id),
                        "media_asset_id": str(payload.media_asset_id),
                        "video_uri": payload.video_uri,
                        "chat_id": str(payload.chat_id) if payload.chat_id else None,
                        "user_id": str(payload.user_id) if payload.user_id else None,
                        "dispatched_at": time.time(),
                        "attempt_no": attempt_no + 1,
                    }
                )
            else:
                runtime_failed_rows.append({"analysis_id": payload.analysis_id, "error": err_text})
                failed_events.append({"payload": payload, "error": str(exc)})

    await asyncio.gather(*[_process_ready(job) for job in ready_jobs])

    async with get_db_connection() as conn:
        if success_rows:
            await update_analysis_status_completed_batch(conn, success_rows)
        all_failed_rows = failed_rows + runtime_failed_rows
        if all_failed_rows:
            await update_analysis_status_failed_batch(conn, all_failed_rows)
        if retry_analysis_ids:
            await update_analysis_status_queued_batch(conn, retry_analysis_ids)
        await conn.commit()

    if retry_payloads:
        batch_size = max(1, int(getattr(settings, "GEMINI_TASK_ENQUEUE_BATCH_SIZE", 100)))
        for idx in range(0, len(retry_payloads), batch_size):
            await cloud_tasks.create_http_task(
                queue_name=settings.QUEUE_GEMINI,
                relative_uri="/v1/tasks/gemini/analyze",
                payload=retry_payloads[idx: idx + batch_size],
            )

    failed_total = len(failed_rows) + len(runtime_failed_rows)
    return _batch_summary(
        route="gemini/analyze",
        processed=len(task_items),
        succeeded=len(success_rows),
        failed=failed_total,
        retried_enqueued=len(retry_payloads),
    )


@router.post("/gemini/analyze")
async def handle_gemini_analysis_task(
    payload: AnalysisTaskPayload | list[AnalysisTaskPayload],
    request: Request,
):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_gemini_analysis_single(items[0], request)
    return await _handle_gemini_analysis_batch(items)


async def _handle_twelvelabs_index_single(payload: TwelveLabsTaskPayload, request: Request) -> dict[str, Any]:
    logger.info("Received TwelveLabs indexing task for %s", payload.media_asset_id)
    executor = CloudTaskExecutor(request)

    start_time = time.time()

    async def _on_fail(e: Exception):
        capture_event_with_error(
            distinct_id="system:twelvelabs",
            event="twelvelabs_index_failed",
            exception=e,
            properties={
                "media_asset_id": str(payload.media_asset_id),
                "duration_ms": int((time.time() - start_time) * 1000),
            },
        )
        async with get_db_connection() as conn:
            await update_twelvelabs_asset_status(
                conn,
                media_asset_id=payload.media_asset_id,
                asset_status="failed",
                index_status="failed",
                error=str(e),
            )
            await conn.commit()

    async with get_db_connection() as conn:
        await update_twelvelabs_asset_status(
            conn,
            media_asset_id=payload.media_asset_id,
            asset_status="processing",
            index_status="processing",
        )
        asset = await get_media_asset_by_id(conn, payload.media_asset_id)
        await conn.commit()

    if not asset:
        await _on_fail(Exception("Media asset not found"))
        return {"status": "failed", "error": "Media asset not found"}

    for attempt in range(18):
        async with get_db_connection() as conn:
            asset = await get_media_asset_by_id(conn, payload.media_asset_id)
            await conn.commit()
        status = asset.get("status", "") if asset else ""
        if status in ("stored", "downloaded"):
            break
        if status == "failed":
            await _on_fail(Exception("Video download failed"))
            return {"status": "failed", "error": "Video download failed"}
        logger.info(
            "Video not ready (status=%s), waiting... attempt %s/18 for TwelveLabs %s",
            status,
            attempt + 1,
            payload.media_asset_id,
        )
        await asyncio.sleep(10)
    else:
        await _on_fail(Exception("Video not ready after 3 min timeout"))
        return {"status": "failed", "error": "Video not ready after timeout"}

    result = await executor.run(
        handler=process_twelvelabs_indexing_by_media_asset,
        on_fail=_on_fail,
        media_asset_id=payload.media_asset_id,
    )
    # Track successful completion
    if result.get("status") == "ok":
        capture_event(
            distinct_id="system:twelvelabs",
            event="twelvelabs_index_completed",
            properties={
                "media_asset_id": str(payload.media_asset_id),
                "duration_ms": int((time.time() - start_time) * 1000),
            },
        )
    return result


@router.post("/twelvelabs/index")
async def handle_twelvelabs_index_task(
    payload: TwelveLabsTaskPayload | list[TwelveLabsTaskPayload],
    request: Request,
):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_twelvelabs_index_single(items[0], request)

    results = []
    for item in items:
        try:
            res = await _handle_twelvelabs_index_single(item, request)
            results.append(res)
        except Exception as exc:
            results.append({"status": "failed", "error": str(exc)})
    succeeded = sum(1 for row in results if row.get("status") == "ok")
    return _batch_summary(
        route="twelvelabs/index",
        processed=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
    )


async def _handle_media_download_single(payload: MediaDownloadTaskPayload, request: Request) -> dict[str, Any]:
    logger.debug("Received single media download task for %s; routing through batch path", payload.asset_id)
    return await _handle_media_download_batch([payload])


async def _handle_media_download_batch(items: list[MediaDownloadTaskPayload]) -> dict[str, Any]:
    if not items:
        return _batch_summary(route="media/download", processed=0, succeeded=0, failed=0)

    by_asset: dict[UUID, MediaDownloadTaskPayload] = {}
    for item in items:
        by_asset[item.asset_id] = item
    task_items = list(by_asset.values())

    async with get_db_connection() as conn:
        claimed = await claim_assets_for_download_batch(conn, [item.asset_id for item in task_items])
        await conn.commit()
    claimed_by_id = {row["id"]: row for row in claimed}

    stored_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    retry_asset_ids: list[UUID] = []
    retry_payloads: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=settings.MEDIA_HTTP_TIMEOUT_S, follow_redirects=True) as client:
        async def _process_claimed(item: MediaDownloadTaskPayload, claimed_asset: dict[str, Any]) -> None:
            started_at = time.time()
            dispatch_to_start_ms = None
            if item.dispatched_at:
                dispatch_to_start_ms = max(0.0, (started_at - float(item.dispatched_at)) * 1000.0)
            if item.priority:
                capture_event(
                    distinct_id="system:media_download",
                    event="media_download_started",
                    properties={
                        "asset_id": str(item.asset_id),
                        "platform": item.platform,
                        "priority": True,
                        "attempt_no": int(item.attempt_no or 0),
                        "dispatch_to_start_ms": dispatch_to_start_ms,
                    },
                )
            try:
                stored = await download_claimed_asset(
                    http_client=client,
                    asset=claimed_asset,
                    platform=item.platform,
                    external_id=item.external_id,
                )
                stored_rows.append(stored)
                finished_at = time.time()
                download_ms = max(0.0, (finished_at - started_at) * 1000.0)
                end_to_end_ms = None
                if item.dispatched_at:
                    end_to_end_ms = max(0.0, (finished_at - float(item.dispatched_at)) * 1000.0)
                if item.priority:
                    capture_event(
                        distinct_id="system:media_download",
                        event="media_download_finished",
                        properties={
                            "asset_id": str(item.asset_id),
                            "platform": item.platform,
                            "priority": True,
                            "attempt_no": int(item.attempt_no or 0),
                            "success": True,
                            "download_ms": download_ms,
                            "end_to_end_ms": end_to_end_ms,
                            "bytes": stored.get("size_bytes"),
                        },
                    )
            except Exception as exc:
                finished_at = time.time()
                download_ms = max(0.0, (finished_at - started_at) * 1000.0)
                end_to_end_ms = None
                if item.dispatched_at:
                    end_to_end_ms = max(0.0, (finished_at - float(item.dispatched_at)) * 1000.0)
                if item.priority:
                    capture_event_with_error(
                        distinct_id="system:media_download",
                        event="media_download_finished",
                        exception=exc,
                        properties={
                            "asset_id": str(item.asset_id),
                            "platform": item.platform,
                            "priority": True,
                            "attempt_no": int(item.attempt_no or 0),
                            "success": False,
                            "download_ms": download_ms,
                            "end_to_end_ms": end_to_end_ms,
                            "error": str(exc)[:200],
                        },
                    )
                attempt_no = int(item.attempt_no or 0)
                if _is_retryable_exception(exc) and (attempt_no + 1) < int(getattr(settings, "TASK_WORKER_MAX_ATTEMPTS", 5)):
                    retry_asset_ids.append(item.asset_id)
                    retry_payloads.append(
                        {
                            "asset_id": str(item.asset_id),
                            "platform": item.platform,
                            "external_id": item.external_id,
                            "priority": item.priority,
                            "attempt_no": attempt_no + 1,
                            "dispatched_at": time.time(),
                        }
                    )
                else:
                    failed_rows.append({"asset_id": item.asset_id, "error": str(exc)})

        await asyncio.gather(
            *[
                _process_claimed(item, claimed_by_id[item.asset_id])
                for item in task_items
                if item.asset_id in claimed_by_id
            ]
        )

    async with get_db_connection() as conn:
        if stored_rows:
            await update_assets_stored_batch(conn, stored_rows)
        if failed_rows:
            await update_assets_failed_batch(conn, failed_rows)
        if retry_asset_ids:
            await reset_assets_pending_batch(conn, retry_asset_ids)
        await conn.commit()

    if retry_payloads:
        priority_retries = [p for p in retry_payloads if p.get("priority")]
        normal_retries = [p for p in retry_payloads if not p.get("priority")]

        if priority_retries:
            batch_size = max(1, int(getattr(settings, "MEDIA_DOWNLOAD_ENQUEUE_BATCH_SIZE", 50)))
            for payload in priority_retries:
                capture_event(
                    distinct_id="system:media_download",
                    event="media_download_dispatched",
                    properties={
                        "asset_id": payload["asset_id"],
                        "platform": payload["platform"],
                        "priority": True,
                        "attempt_no": payload["attempt_no"],
                        "dispatched_at": payload.get("dispatched_at"),
                        "source": "media_download_retry",
                    },
                )
            for idx in range(0, len(priority_retries), batch_size):
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_MEDIA_DOWNLOAD_PRIORITY,
                    relative_uri="/v1/tasks/media/download",
                    payload=priority_retries[idx: idx + batch_size],
                )

        # Normal retries are enqueued one asset per task to keep memory/throughput pressure low.
        for payload in normal_retries:
            await cloud_tasks.create_http_task(
                queue_name=settings.QUEUE_MEDIA_DOWNLOAD,
                relative_uri="/v1/tasks/media/download",
                payload=payload,
            )

    # Unclaimed assets are treated as successful no-op (already processing/stored/failed).
    succeeded = len(stored_rows) + (len(task_items) - len(claimed_by_id))
    failed = len(failed_rows)
    return _batch_summary(
        route="media/download",
        processed=len(task_items),
        succeeded=succeeded,
        failed=failed,
        retried_enqueued=len(retry_payloads),
    )


@router.post("/media/download")
async def handle_media_download_task(
    payload: MediaDownloadTaskPayload | list[MediaDownloadTaskPayload],
    request: Request,
):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_media_download_single(items[0], request)
    return await _handle_media_download_batch(items)


async def _handle_raw_archive_single(payload: RawArchiveTaskPayload, request: Request) -> dict[str, Any]:
    from app.storage.raw_archive import upload_raw_compressed, upload_raw_json_gz

    logger.debug("Received raw archive task for search %s platform %s", payload.search_id, payload.platform)
    executor = CloudTaskExecutor(request)

    start_time = time.time()

    async def _on_fail(e: Exception):
        logger.error("Raw archive permanently failed for search %s", payload.search_id)
        capture_event_with_error(
            distinct_id="system:raw_archive",
            event="raw_archive_failed",
            exception=e,
            properties={
                "search_id": str(payload.search_id),
                "platform": payload.platform,
                "duration_ms": int((time.time() - start_time) * 1000),
            },
        )

    if payload.raw_json is not None:
        result = await executor.run(
            handler=upload_raw_json_gz,
            on_fail=_on_fail,
            platform=payload.platform,
            search_id=payload.search_id,
            raw_json=payload.raw_json,
            key_override=payload.gcs_key,
        )
        # Track successful completion
        if result.get("status") == "ok":
            capture_event(
                distinct_id="system:raw_archive",
                event="raw_archive_completed",
                properties={
                    "search_id": str(payload.search_id),
                    "platform": payload.platform,
                    "duration_ms": int((time.time() - start_time) * 1000),
                },
            )
        return result

    if payload.raw_json_compressed:
        compressed_bytes = base64.b64decode(payload.raw_json_compressed)
        result = await executor.run(
            handler=upload_raw_compressed,
            on_fail=_on_fail,
            platform=payload.platform,
            search_id=payload.search_id,
            compressed_data=compressed_bytes,
            key_override=payload.gcs_key,
        )
        # Track successful completion
        if result.get("status") == "ok":
            capture_event(
                distinct_id="system:raw_archive",
                event="raw_archive_completed",
                properties={
                    "search_id": str(payload.search_id),
                    "platform": payload.platform,
                    "duration_ms": int((time.time() - start_time) * 1000),
                },
            )
        return result

    raise ValueError("raw archive payload missing both raw_json and raw_json_compressed")


@router.post("/raw/archive")
async def handle_raw_archive_task(payload: RawArchiveTaskPayload | list[RawArchiveTaskPayload], request: Request):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_raw_archive_single(items[0], request)
    results = await asyncio.gather(*[_handle_raw_archive_single(item, request) for item in items], return_exceptions=True)
    succeeded = sum(1 for row in results if isinstance(row, dict) and row.get("status") == "ok")
    return _batch_summary(
        route="raw/archive",
        processed=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
    )


async def _handle_board_insights_single(payload: BoardInsightsTaskPayload, request: Request) -> dict[str, Any]:
    from app.db import set_rls_user
    from app.db.queries import get_board_insights

    logger.info("Received board insights task for board %s", payload.board_id)
    executor = CloudTaskExecutor(request)

    start_time = time.time()

    async def _on_fail(e: Exception):
        capture_event_with_error(
            distinct_id=str(payload.user_id),
            event="board_insights_failed",
            exception=e,
            properties={
                "board_id": str(payload.board_id),
                "duration_ms": int((time.time() - start_time) * 1000),
            },
        )
        async with get_db_connection() as conn:
            await set_rls_user(conn, payload.user_id)
            row = await get_board_insights(conn, payload.board_id)
            if row:
                await update_board_insights_status(
                    conn,
                    insights_id=row["id"],
                    status="failed",
                    error=str(e),
                )
                await conn.commit()

    async with get_db_connection() as conn:
        await set_rls_user(conn, payload.user_id)
        row = await get_board_insights(conn, payload.board_id)
        if row and row.get("status") == "queued":
            await update_board_insights_status(conn, insights_id=row["id"], status="processing")
            await conn.commit()

    result = await executor.run(
        handler=execute_board_insights,
        on_fail=_on_fail,
        board_id=payload.board_id,
        user_id=payload.user_id,
        user_role=payload.user_role,
    )
    # Track successful completion
    if result.get("status") == "ok":
        capture_event(
            distinct_id=str(payload.user_id),
            event="board_insights_completed",
            properties={
                "board_id": str(payload.board_id),
                "duration_ms": int((time.time() - start_time) * 1000),
            },
        )
    return result


@router.post("/boards/insights")
async def handle_board_insights_task(
    payload: BoardInsightsTaskPayload | list[BoardInsightsTaskPayload],
    request: Request,
):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_board_insights_single(items[0], request)
    results = await asyncio.gather(*[_handle_board_insights_single(item, request) for item in items], return_exceptions=True)
    succeeded = sum(1 for row in results if isinstance(row, dict) and row.get("status") == "ok")
    return _batch_summary(
        route="boards/insights",
        processed=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
    )


async def _handle_search_run_single(payload: SearchTaskPayload, request: Request) -> dict[str, Any]:
    logger.info("Received search task for %s", payload.search_id)
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        logger.error("Search task permanently failed for %s: %s", payload.search_id, e)

    return await executor.run(
        handler=search_worker,
        on_fail=_on_fail,
        search_id=payload.search_id,
        user_uuid=payload.user_uuid,
        query=payload.query,
        inputs=payload.inputs,
        redis_client=_get_request_redis(request),
        dispatched_at=payload.dispatched_at,
    )


@router.post("/search/run")
async def handle_search_task(payload: SearchTaskPayload | list[SearchTaskPayload], request: Request):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_search_run_single(items[0], request)
    results = await asyncio.gather(*[_handle_search_run_single(item, request) for item in items], return_exceptions=True)
    succeeded = sum(1 for row in results if isinstance(row, dict) and row.get("status") == "ok")
    return _batch_summary(
        route="search/run",
        processed=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
    )


async def _handle_load_more_single(payload: LoadMoreTaskPayload, request: Request) -> dict[str, Any]:
    logger.info("Received load_more task for %s", payload.search_id)
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        logger.error("Load more task permanently failed for %s: %s", payload.search_id, e)

    return await executor.run(
        handler=load_more_worker,
        on_fail=_on_fail,
        search_id=payload.search_id,
        user_uuid=payload.user_uuid,
        query=payload.query,
        platform_cursors=payload.platform_cursors,
        redis_client=_get_request_redis(request),
    )


@router.post("/search/load_more")
async def handle_load_more_task(payload: LoadMoreTaskPayload | list[LoadMoreTaskPayload], request: Request):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_load_more_single(items[0], request)
    results = await asyncio.gather(*[_handle_load_more_single(item, request) for item in items], return_exceptions=True)
    succeeded = sum(1 for row in results if isinstance(row, dict) and row.get("status") == "ok")
    return _batch_summary(
        route="search/load_more",
        processed=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
    )


async def _handle_chat_stream_single(payload: ChatStreamTaskPayload, request: Request) -> dict[str, Any]:
    logger.info("Received chat stream task for %s", payload.chat_id)
    logger.info("Received chat stream task filters=%s", payload.filters)
    executor = CloudTaskExecutor(request)
    telemetry_ctx = telemetry_from_mapping(payload.model_dump(exclude_none=True))
    telemetry_ctx = merge_telemetry(
        telemetry_ctx,
        feature=payload.feature or "chat",
        operation=payload.operation or "stream_response",
        subject_type=payload.subject_type or "chat_message",
        subject_id=payload.subject_id or payload.message_client_id,
        message_client_id=payload.message_client_id,
        user_id=str(payload.user_id) if payload.user_id else telemetry_ctx.user_id,
        task_retry_count=executor.retry_count,
    )

    async def _on_fail(e: Exception):
        logger.error("Chat stream task permanently failed for %s: %s", payload.chat_id, e)
        try:
            redis_client = _get_request_redis(request)
        except RuntimeError as exc:
            logger.warning("Redis client unavailable for chat stream error: %s", exc)
            return
        await redis_client.xadd(
            f"chat:{str(payload.chat_id)}:stream",
            {"data": json.dumps({"type": "error", "error": str(e)})},
            maxlen=settings.REDIS_STREAM_MAXLEN_CHAT,
            approximate=True,
        )
        await redis_client.expire(
            f"chat:{str(payload.chat_id)}:stream",
            settings.REDIS_STREAM_TTL_S_CHAT,
        )

    async def _run_chat_stream():
        graph, saver_cm = await create_agent_graph(settings.DATABASE_URL)
        try:
            redis_client = _get_request_redis(request)
            await stream_generator_to_redis(
                graph=graph,
                chat_id=str(payload.chat_id),
                thread_id=payload.thread_id,
                inputs=payload.inputs,
                context={"x-auth-token": payload.auth_token} if payload.auth_token else None,
                model_name=payload.model_name,
                image_urls=payload.image_urls or [],
                filters=payload.filters or {},
                user_id=str(payload.user_id) if payload.user_id else None,
                redis_client=redis_client,
                telemetry=telemetry_ctx,
            )
        finally:
            try:
                await saver_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Failed to close chat saver context: %s", e)

    with bind_telemetry(telemetry_ctx):
        return await executor.run(handler=_run_chat_stream, on_fail=_on_fail)


@router.post("/chats/stream")
async def handle_chat_stream_task(payload: ChatStreamTaskPayload | list[ChatStreamTaskPayload], request: Request):
    items, is_single = _normalize_payload(payload)
    if is_single:
        return await _handle_chat_stream_single(items[0], request)
    results = await asyncio.gather(*[_handle_chat_stream_single(item, request) for item in items], return_exceptions=True)
    succeeded = sum(1 for row in results if isinstance(row, dict) and row.get("status") == "ok")
    return _batch_summary(
        route="chats/stream",
        processed=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
    )
