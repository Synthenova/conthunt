import logging
import httpx
from typing import Callable, Any, Optional
from fastapi import Request

logger = logging.getLogger(__name__)

class CloudTaskExecutor:
    """
    Executes a task handler with built-in retry logic compatible with Google Cloud Tasks.
    
    If the handler raises a 'retryable' exception and we haven't hit max_retries,
    this executor will re-raise the exception (causing Cloud Tasks to retry).
    
    If the exception is not retryable OR we hit max_retries, it calls the 
    on_fail callback (to update DB status) and returns 200 OK (stopping Cloud Tasks).
    """
    
    def __init__(self, request: Request, max_retries: int = 5):
        # Header is set by Cloud Tasks: 0, 1, 2...
        self.retry_count = int(request.headers.get("X-CloudTasks-TaskRetryCount", 0))
        self.max_retries = max_retries

    async def run(
        self, 
        handler: Callable, 
        on_fail: Callable, 
        *args, 
        **kwargs
    ):
        try:
            # Execute the business logic
            await handler(*args, **kwargs)
            return {"status": "ok"}
            
        except Exception as e:
            if self._should_retry(e) and self.retry_count < self.max_retries:
                logger.warning(
                    f"Task failed (attempt {self.retry_count + 1}/{self.max_retries + 1}), retrying. Error: {e}"
                )
                # Re-raise to trigger Cloud Tasks retry (needs non-2xx response)
                raise e 
            
            # Final failure handling (Stop Retrying)
            logger.error(
                f"Task failed permanently after {self.retry_count + 1} attempts. Stops retrying. Error: {type(e).__name__}: {e}"
            )
            
            try:
                # Update DB status or cleanup
                await on_fail(e)
            except Exception as fail_handler_err:
                logger.error(f"Failed to execute failure handler: {fail_handler_err}")
                
            # Return 200 OK to stop Cloud Tasks from retrying further
            return {"status": "failed", "error": str(e)}

    def _should_retry(self, e: Exception) -> bool:
        """
        Determine if exception is transient/retryable.
        """
        # HTTP Network/Timeout errors are retryable
        if isinstance(e, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
            return True
            
        # HTTP Status errors (5xx, 429) are retryable
        if isinstance(e, httpx.HTTPStatusError):
            if e.response.status_code >= 500 or e.response.status_code == 429:
                return True
            # 4xx are usually logical errors (not retryable)
            return False
            
        # Generic ValueErrors/TypeErrors are usually code bugs (not retryable)
        if isinstance(e, (ValueError, TypeError, KeyError)):
            return False
            
        # Default: Retry other unforeseen exceptions (conservative approach for background tasks)
        # to handle sporadic DB connection issues, etc.
        return True
