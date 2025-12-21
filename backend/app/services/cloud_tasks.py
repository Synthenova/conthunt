
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
            logger.warning(f"[LOCAL] Skipping Cloud Task creation for {relative_uri} in queue {queue_name}")
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

# Global instance
cloud_tasks = CloudTasksService()
