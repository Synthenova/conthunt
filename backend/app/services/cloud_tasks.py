
import json
import time
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from app.core import get_settings, logger

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
        """
        try:
            if not payload:
                 payload = {}
                 
            if uri == "/v1/tasks/gemini/analyze":
                from app.api.v1.analysis import _execute_gemini_analysis
                from uuid import UUID
                await _execute_gemini_analysis(
                    analysis_id=UUID(payload["analysis_id"]),
                    media_asset_id=UUID(payload["media_asset_id"]),
                    video_uri=payload["video_uri"]
                )
                
            elif uri == "/v1/tasks/twelvelabs/index":
                from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
                from uuid import UUID
                await process_twelvelabs_indexing_by_media_asset(
                    media_asset_id=UUID(payload["media_asset_id"])
                )
                
            elif uri == "/v1/tasks/media/download":
                from app.media.downloader import download_asset_with_claim
                from uuid import UUID
                import httpx
                
                async with httpx.AsyncClient(timeout=self.settings.MEDIA_HTTP_TIMEOUT_S, follow_redirects=True) as client:
                    await download_asset_with_claim(
                        http_client=client,
                        asset_id=UUID(payload["asset_id"]),
                        platform=payload["platform"],
                        external_id=payload["external_id"]
                    )
            
            elif uri == "/v1/tasks/raw/archive":
                from app.storage.raw_archive import upload_raw_compressed
                from uuid import UUID
                import base64
                
                # Decode base64 to get compressed bytes (already gzipped)
                compressed_bytes = base64.b64decode(payload["raw_json_compressed"])
                
                await upload_raw_compressed(
                    platform=payload["platform"],
                    search_id=UUID(payload["search_id"]),
                    compressed_data=compressed_bytes
                )
                
            elif uri == "/v1/tasks/boards/insights":
                from app.services.board_insights import execute_board_insights
                from uuid import UUID
                
                await execute_board_insights(
                    board_id=UUID(payload["board_id"]),
                    user_id=UUID(payload["user_id"]),
                )
                
            else:
                logger.warning(f"[LOCAL] Unknown task URI: {uri}")
                
        except Exception as e:
            logger.error(f"[LOCAL] Background task failed for {uri}: {e}", exc_info=True)

# Global instance
cloud_tasks = CloudTasksService()
