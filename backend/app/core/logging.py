"""Logging configuration."""
import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("conthunt")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


    return logger


def get_log_level() -> str:
    # Avoid circular imports by reading env directly
    import os
    from dotenv import load_dotenv
    
    # Try to load .env if it exists
    load_dotenv()
    
    return os.getenv("LOG_LEVEL", "INFO")


logger = setup_logging(get_log_level())
