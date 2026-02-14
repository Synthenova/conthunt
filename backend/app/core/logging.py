"""Logging configuration."""
import logging
import sys

from opentelemetry.instrumentation.logging import LoggingInstrumentor
from app.core.telemetry_context import get_current_telemetry


class TelemetryLogFilter(logging.Filter):
    """Inject request telemetry fields into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = get_current_telemetry()
        record.action_id = ctx.action_id or "-"
        record.session_id = ctx.session_id or "-"
        record.attempt_no = ctx.attempt_no if ctx.attempt_no is not None else "-"
        record.user_id = ctx.user_id or "-"
        record.feature = ctx.feature or "-"
        record.operation = ctx.operation or "-"
        record.subject_type = ctx.subject_type or "-"
        record.subject_id = ctx.subject_id or "-"
        return True


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""
    LoggingInstrumentor().instrument(set_logging_format=False)
    logger = logging.getLogger("conthunt")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.addFilter(TelemetryLogFilter())
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d "
            "| trace=%(otelTraceID)s span=%(otelSpanID)s sampled=%(otelTraceSampled)s "
            "| action=%(action_id)s session=%(session_id)s attempt=%(attempt_no)s "
            "| user=%(user_id)s feature=%(feature)s op=%(operation)s subject=%(subject_type)s:%(subject_id)s "
            "- %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_log_level() -> str:
    # Avoid circular imports by reading env directly
    import os
    from dotenv import load_dotenv
    
    # Try to load .env if it exists
    load_dotenv()
    
    return os.getenv("LOG_LEVEL", "INFO")


logger = setup_logging(get_log_level())
