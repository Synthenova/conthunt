
import json
import time
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from app.core import get_settings, logger
from app.db.session import get_db_connection

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

    async def create_http_task(
        self,
        queue_name: str,
        relative_uri: str,
        payload: dict | None = None,
        schedule_seconds: int | None = None
    ) -> str:
        """
        Create a secure HTTP task on Cloud Tasks.
        """
        if not self.settings.API_BASE_URL or "localhost" in self.settings.API_BASE_URL:
            # Local development: Dispatch directly to background function
            logger.info(f"[LOCAL] Dispatching background task for {relative_uri} in queue {queue_name}")
            import asyncio
            asyncio.create_task(self._run_local_task(relative_uri, payload))
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

        try:
            response = self.client.create_task(request={"parent": parent, "task": task})
            logger.info(f"Created task {response.name} for {relative_uri} in {queue_name}")
            return response.name
        except Exception as e:
            logger.error(f"Failed to create cloud task: {e}")
            raise e

    async def _run_local_task(self, uri: str, payload: dict | None):
        """
        Execute task logic locally (mirroring app/api/v1/tasks.py).
        All tasks have proper error handling to mark DB status as failed.
        """
        from uuid import UUID
        
        if not payload:
            payload = {}
             
        if uri == "/v1/tasks/gemini/analyze":
            from app.api.v1.analysis import _execute_gemini_analysis
            from app.db.queries.analysis import update_analysis_status
            from app.db.queries.content import get_media_asset_by_id
            import asyncio
            
            analysis_id = UUID(payload["analysis_id"])
            media_asset_id = UUID(payload["media_asset_id"])
            try:
                # Mark as processing on pickup
                async with get_db_connection() as conn:
                    await update_analysis_status(conn, analysis_id, status="processing")
                    await conn.commit()
                
                # Check if YouTube (no wait needed)
                async with get_db_connection() as conn:
                    asset = await get_media_asset_by_id(conn, media_asset_id)
                source_url = asset.get("source_url", "") if asset else ""
                is_youtube = "youtube.com" in source_url or "youtu.be" in source_url
                
                # Wait for video to be ready (max 3 min) - non-YouTube only
                if not is_youtube:
                    for attempt in range(18):
                        async with get_db_connection() as conn:
                            asset = await get_media_asset_by_id(conn, media_asset_id)
                        status = asset.get("status", "") if asset else ""
                        if status in ("stored", "downloaded"):
                            break
                        if status == "failed":
                            raise Exception("Video download failed")
                        logger.info(f"[LOCAL] Video not ready (status={status}), waiting... {attempt+1}/18")
                        await asyncio.sleep(10)
                    else:
                        raise Exception("Video not ready after 3 min timeout")
                
                await _execute_gemini_analysis(
                    analysis_id=analysis_id,
                    media_asset_id=media_asset_id,
                    video_uri=payload["video_uri"]
                )
            except Exception as e:
                logger.error(f"[LOCAL] Gemini analysis failed: {e}", exc_info=True)
                async with get_db_connection() as conn:
                    await update_analysis_status(conn, analysis_id, status="failed", error=str(e))
                    await conn.commit()
                
        elif uri == "/v1/tasks/twelvelabs/index":
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
                
        elif uri == "/v1/tasks/media/download":
            from app.media.downloader import download_asset_with_claim, update_asset_failed
            import httpx

            asset_id = UUID(payload["asset_id"])
            is_priority = payload.get("priority", False)
            async with httpx.AsyncClient(timeout=self.settings.MEDIA_HTTP_TIMEOUT_S, follow_redirects=True) as client:
                try:
                    await download_asset_with_claim(
                        http_client=client,
                        asset_id=asset_id,
                        platform=payload["platform"],
                        external_id=payload["external_id"],
                        skip_semaphore=is_priority,
                    )
                except Exception as e:
                    logger.error(f"[LOCAL] Media download failed: {e}", exc_info=True)
                    async with get_db_connection() as conn:
                        await update_asset_failed(conn, asset_id, str(e))
        
        elif uri == "/v1/tasks/raw/archive":
            from app.storage.raw_archive import upload_raw_compressed
            import base64
            
            try:
                compressed_bytes = base64.b64decode(payload["raw_json_compressed"])
                await upload_raw_compressed(
                    platform=payload["platform"],
                    search_id=UUID(payload["search_id"]),
                    compressed_data=compressed_bytes
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
            try:
                # Mark as processing on pickup
                async with get_db_connection() as conn:
                    await set_rls_user(conn, user_id)
                    row = await get_board_insights(conn, board_id)
                    if row:
                        await update_board_insights_status(conn, insights_id=row["id"], status="processing")
                        await conn.commit()
                
                await execute_board_insights(board_id=board_id, user_id=user_id)
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
                
        else:
            logger.warning(f"[LOCAL] Unknown task URI: {uri}")

# Global instance
cloud_tasks = CloudTasksService()
