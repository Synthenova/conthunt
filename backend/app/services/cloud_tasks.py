
import asyncio
import json
import time
from google.cloud import tasks_v2
from google.protobuf import duration_pb2
from google.protobuf import timestamp_pb2

from app.core import get_settings, logger
from app.core.telemetry import trace_span
from app.db.session import get_db_connection
from app.db.db_semaphore import db_kind_override


class CloudTasksService:
    def __init__(self):
        self.settings = get_settings()
        self.client = tasks_v2.CloudTasksClient()

    def get_parent(self, queue_name: str) -> str:
        return self.client.queue_path(
            self.settings.GCP_PROJECT,
            self.settings.GCP_REGION,
            queue_name
        )

    @trace_span("cloud_tasks.create_http_task")
    async def create_http_task(
        self,
        queue_name: str,
        relative_uri: str,
        payload: dict | list[dict] | None = None,
        schedule_seconds: int | None = None,
        dispatch_deadline_seconds: int | None = None,
    ) -> str:
        """
        Create a secure HTTP task on Cloud Tasks.
        """
        if not self.settings.API_BASE_URL or "localhost" in self.settings.API_BASE_URL:            
            import asyncio
            async def _run():
                # Local task execution
                # Ensure DB slots are charged against the "tasks" semaphore key, not the
                # originating API request context.
                with db_kind_override("tasks"):
                    await self._run_local_task(relative_uri, payload)

            asyncio.create_task(_run())
            return "local-task-id"

        url = f"{self.settings.API_BASE_URL}{relative_uri}"
        parent = self.get_parent(queue_name)
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": {"Content-Type": "application/json"},
                "oidc_token": {
                    "service_account_email": self.settings.CLOUD_TASKS_SA_EMAIL,
                },
            }
        }

        if payload:
            task["http_request"]["body"] = json.dumps(payload).encode()

        if schedule_seconds:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromSeconds(int(time.time() + schedule_seconds))
            task["schedule_time"] = timestamp

        if dispatch_deadline_seconds:
            # Cloud Tasks dispatch deadline must be >= handler runtime; Cloud Run timeout
            # should be configured to be >= this value as well.
            task["dispatch_deadline"] = duration_pb2.Duration(seconds=int(dispatch_deadline_seconds))

        try:
            response = self.client.create_task(request={"parent": parent, "task": task})
            logger.debug(f"Created task {response.name} for {relative_uri} in {queue_name}")
            return response.name
        except Exception as e:
            logger.error(f"Failed to create cloud task: {e}")
            raise e

    @trace_span("cloud_tasks.run_local_task")
    async def _run_local_task(self, uri: str, payload: dict | list[dict] | None):
        """
        Execute task logic locally (mirroring app/api/v1/tasks.py).
        All tasks have proper error handling to mark DB status as failed.
        """
        from uuid import UUID
        
        if payload is None:
            payload = {}

        if uri == "/v1/tasks/gemini/analyze":
            from app.api.v1.tasks import AnalysisTaskPayload, _handle_gemini_analysis_batch

            payloads = payload if isinstance(payload, list) else [payload]
            parsed = [AnalysisTaskPayload.model_validate(item or {}) for item in payloads]
            await _handle_gemini_analysis_batch(parsed)
            return

        if uri == "/v1/tasks/media/download":
            from app.api.v1.tasks import MediaDownloadTaskPayload, _handle_media_download_batch

            payloads = payload if isinstance(payload, list) else [payload]
            parsed = [MediaDownloadTaskPayload.model_validate(item or {}) for item in payloads]
            await _handle_media_download_batch(parsed)
            return

        if isinstance(payload, list):
            for item in payload:
                await self._run_local_task(uri, item)
            return
             
        if uri == "/v1/tasks/twelvelabs/index":
            from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
            from app.db.queries import update_twelvelabs_asset_status
            from app.db.queries.content import get_media_asset_by_id
            import asyncio
            
            media_asset_id = UUID(payload["media_asset_id"])
            try:
                # Mark as processing on pickup
                async with get_db_connection() as conn:
                    await update_twelvelabs_asset_status(
                        conn, media_asset_id=media_asset_id,
                        asset_status="processing", index_status="processing"
                    )
                    await conn.commit()
                
                # Wait for video to be ready (max 3 min)
                for attempt in range(18):
                    async with get_db_connection() as conn:
                        asset = await get_media_asset_by_id(conn, media_asset_id)
                    status = asset.get("status", "") if asset else ""
                    if status in ("stored", "downloaded"):
                        break
                    if status == "failed":
                        raise Exception("Video download failed")
                    logger.info(f"[LOCAL] Video not ready (status={status}), waiting for TwelveLabs... {attempt+1}/18")
                    await asyncio.sleep(10)
                else:
                    raise Exception("Video not ready after 3 min timeout")
                
                await process_twelvelabs_indexing_by_media_asset(media_asset_id=media_asset_id)
            except Exception as e:
                logger.error(f"[LOCAL] TwelveLabs indexing failed: {e}", exc_info=True)
                async with get_db_connection() as conn:
                    await update_twelvelabs_asset_status(
                        conn, media_asset_id=media_asset_id,
                        asset_status="failed", index_status="failed", error=str(e)
                    )
                    await conn.commit()
                
        elif uri == "/v1/tasks/raw/archive":
            from app.storage.raw_archive import upload_raw_compressed
            import base64
            
            try:
                compressed_bytes = base64.b64decode(payload["raw_json_compressed"])
                await upload_raw_compressed(
                    platform=payload["platform"],
                    search_id=UUID(payload["search_id"]),
                    compressed_data=compressed_bytes,
                    key_override=payload.get("gcs_key"),
                )
            except Exception as e:
                logger.error(f"[LOCAL] Raw archive failed: {e}", exc_info=True)
                # No DB row for raw archive - just log
                
        elif uri == "/v1/tasks/boards/insights":
            from app.services.board_insights import execute_board_insights
            from app.db.queries import get_board_insights, update_board_insights_status
            from app.db import set_rls_user
            
            board_id = UUID(payload["board_id"])
            user_id = UUID(payload["user_id"])
            user_role = payload.get("user_role", "free")
            try:
                # Mark as processing on pickup
                async with get_db_connection() as conn:
                    await set_rls_user(conn, user_id)
                    row = await get_board_insights(conn, board_id)
                    if row:
                        await update_board_insights_status(conn, insights_id=row["id"], status="processing")
                        await conn.commit()
                
                await execute_board_insights(
                    board_id=board_id,
                    user_id=user_id,
                    user_role=user_role,
                )
            except Exception as e:
                logger.error(f"[LOCAL] Board insights failed: {e}", exc_info=True)
                async with get_db_connection() as conn:
                    await set_rls_user(conn, user_id)
                    row = await get_board_insights(conn, board_id)
                    if row:
                        await update_board_insights_status(
                            conn, insights_id=row["id"], status="failed", error=str(e)
                        )
                        await conn.commit()

        elif uri == "/v1/tasks/search/run":
            from app.api.v1.search import search_worker

            search_id = UUID(payload["search_id"])
            user_uuid = UUID(payload["user_uuid"])
            try:
                from app.core.redis_client import get_redis_from_state
                from app.main import app as main_app
                redis_client = get_redis_from_state(main_app.state)
                await search_worker(
                    search_id=search_id,
                    user_uuid=user_uuid,
                    query=payload["query"],
                    inputs=payload["inputs"],
                    redis_client=redis_client,
                )
            except Exception as e:
                logger.error(f"[LOCAL] Search worker failed: {e}", exc_info=True)

        elif uri == "/v1/tasks/search/load_more":
            from app.api.v1.search import load_more_worker

            search_id = UUID(payload["search_id"])
            user_uuid = UUID(payload["user_uuid"])
            try:
                from app.core.redis_client import get_redis_from_state
                from app.main import app as main_app
                redis_client = get_redis_from_state(main_app.state)
                await load_more_worker(
                    search_id=search_id,
                    user_uuid=user_uuid,
                    query=payload["query"],
                    platform_cursors=payload["platform_cursors"],
                    redis_client=redis_client,
                )
            except Exception as e:
                logger.error(f"[LOCAL] Load more worker failed: {e}", exc_info=True)

        elif uri == "/v1/tasks/chats/stream":
            from app.api.v1.chats import stream_generator_to_redis
            from app.agent.runtime import create_agent_graph
            from app.core.redis_client import get_redis_from_state
            from app.core.telemetry_context import merge_telemetry, telemetry_from_mapping

            chat_id = UUID(payload["chat_id"])
            try:
                graph, saver_cm = await create_agent_graph(self.settings.DATABASE_URL)
                try:
                    from app.main import app as main_app
                    redis_client = get_redis_from_state(main_app.state)
                    telemetry_ctx = merge_telemetry(
                        telemetry_from_mapping(payload),
                        feature=payload.get("feature") or "chat",
                        operation=payload.get("operation") or "stream_response",
                        subject_type=payload.get("subject_type") or "chat_message",
                        subject_id=payload.get("subject_id") or payload.get("message_client_id"),
                        message_client_id=payload.get("message_client_id"),
                    )
                    await stream_generator_to_redis(
                        graph=graph,
                        chat_id=str(chat_id),
                        thread_id=payload["thread_id"],
                        inputs=payload["inputs"],
                        context={"x-auth-token": payload.get("auth_token")} if payload.get("auth_token") else None,
                        model_name=payload.get("model_name"),
                        image_urls=payload.get("image_urls") or [],
                        filters=payload.get("filters") or {},
                        user_id=payload.get("user_id"),
                        redis_client=redis_client,
                        telemetry=telemetry_ctx,
                    )
                finally:
                    try:
                        await saver_cm.__aexit__(None, None, None)
                    except Exception as e:
                        logger.warning(f"[LOCAL] Failed to close chat saver context: {e}")
            except Exception as e:
                logger.error(f"[LOCAL] Chat stream failed: {e}", exc_info=True)
                try:
                    from app.main import app as main_app
                    redis_client = get_redis_from_state(main_app.state)
                    from app.core import get_settings
                    settings = get_settings()
                    await redis_client.xadd(
                        f"chat:{str(chat_id)}:stream",
                        {"data": json.dumps({"type": "error", "error": str(e)})},
                        maxlen=settings.REDIS_STREAM_MAXLEN_CHAT,
                        approximate=True,
                    )
                    await redis_client.expire(
                        f"chat:{str(chat_id)}:stream",
                        settings.REDIS_STREAM_TTL_S_CHAT,
                    )
                except Exception as exc:
                    logger.warning("[LOCAL] Redis unavailable for chat error: %s", exc)
                
        else:
            logger.warning(f"[LOCAL] Unknown task URI: {uri}")

# Global instance
cloud_tasks = CloudTasksService()
