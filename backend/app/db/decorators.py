import functools
import time
import logging

from app.core.logging import logger

def log_query_timing(func):
    """Decorator to log start and end time of SQL operations."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()
        logger.info(f"Starting SQL operation: {func_name}")
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Completed SQL operation: {func_name} in {duration:.4f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed SQL operation: {func_name} in {duration:.4f}s with error: {str(e)}")
            raise e
            
    return wrapper
