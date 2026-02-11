"""Application settings loaded from environment variables."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    APP_ENV: str
    DATABASE_URL: str
    DB_SCHEMA: str = "conthunt"
    # PgBouncer transaction pooling requires avoiding per-session state and prepared statement caches.
    # Values: "session" or "transaction"
    DB_PGBOUNCER_MODE: str = "session"
    # If true, disable SQLAlchemy pooling and rely on PgBouncer for pooling/multiplexing.
    # This avoids app-side QueuePool timeouts under high concurrency (e.g., deep research fanout).
    DB_USE_NULLPOOL: bool = True
    # Global DB backpressure (Redis ZSET + Lua). Fail-open by design if Redis is down.
    DB_SEMAPHORE_ENABLED: bool = True
    DB_SEM_KEY_PREFIX: str = "sem:db"
    DB_SEM_TTL_MS: int = 10_000
    DB_SEM_API_LIMIT: int = 7
    DB_SEM_TASKS_LIMIT: int = 13
    # Wait budgets for acquiring a DB slot. Keep these large enough to queue under burst
    # instead of failing fast with 429/503.
    DB_SEM_API_MAX_WAIT_MS: int = 5_000
    DB_SEM_TASKS_MAX_WAIT_MS: int = 20_000
    # Cloud Run can scale horizontally; keep per-instance pools small to avoid exceeding
    # Cloud SQL connection caps when max instances are active.
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 10
    LOG_LEVEL: str = "DEBUG"
    
    # GCP / Firebase
    GCLOUD_PROJECT: str = "conthunt-dev"
    GCP_PROJECT: str = "conthunt-dev"
    GCP_REGION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS_FB: str = ""
    # GOOGLE_API_KEY: str
    
    # Cloud Tasks
    CLOUD_TASKS_SA_EMAIL: str = "tasks-invoker@conthunt-dev.iam.gserviceaccount.com"
    API_BASE_URL: str = "https://api.conthunt.com"

    
    # queues
    QUEUE_MEDIA_DOWNLOAD: str = "media-download-queue"
    QUEUE_TWELVELABS: str = "twelvelabs-queue"
    QUEUE_GEMINI: str = "gemini-queue"
    QUEUE_RAW_ARCHIVE: str = "raw-archive-queue"
    QUEUE_MEDIA_DOWNLOAD_PRIORITY: str = "media-download-priority"
    QUEUE_SEARCH_WORKER: str = "search-worker-queue"
    QUEUE_CHAT_STREAM: str = "chat-stream-queue"

    # Deep research tuning
    DEEP_RESEARCH_ANALYSIS_CONCURRENCY: int = 10
    DEEP_RESEARCH_SEARCH_CONCURRENCY: int = 5
    DEEP_RESEARCH_MODEL: str = "openrouter/google/gemini-3-flash-preview"
    LANGGRAPH_RECURSION_LIMIT: int = 100
    # If true, stream all LangGraph events to Redis during deep research (very noisy; expensive).
    DEEP_RESEARCH_STREAM_DEBUG_EVENTS: bool = False
    # Deep research analysis waiting behavior (agent tool).
    # We poll Postgres for completion (no SSE/Redis dependency); keep this bounded.
    DEEP_RESEARCH_ANALYSIS_POLL_TIMEOUT_S: float = 240.0
    # Delay first poll after triggering analysis, then poll at a fixed cadence.
    DEEP_RESEARCH_ANALYSIS_POLL_FIRST_DELAY_S: float = 40.0
    DEEP_RESEARCH_ANALYSIS_POLL_INTERVAL_S: float = 5.0

    # ScrapeCreators API
    SCRAPECREATORS_API_KEY: str
    SCRAPECREATORS_BASE_URL: str = "https://api.scrapecreators.com"

    # GCS Buckets
    GCS_BUCKET_RAW: str = "conthunt-dev-raw"
    GCS_BUCKET_MEDIA: str = "conthunt-dev-media"
    GCS_DEEPAGNT_FS: str = "conthunt-dev-deepagent-fs"
    # Local signing only: absolute path to a service account JSON key file.
    # Example (Cloud Run secret mount): /secrets/gcs_signer.json
    GCS_SIGNER_KEY_PATH: str = ""

    # Media download behavior
    MEDIA_DOWNLOAD_ENABLED: bool = True
    MEDIA_MAX_CONCURRENCY: int = 4
    MEDIA_HTTP_TIMEOUT_S: int = 60
    MEDIA_OPTIMIZE_IMAGES: bool = True
    MEDIA_IMAGE_FORMAT: str = "webp"  # webp or jpeg
    MEDIA_IMAGE_QUALITY: int = 75
    RAW_UPLOAD_ENABLED: bool = True

    # TwelveLabs Video Analysis
    TWELVELABS_API_KEY: str = ""
    TWELVELABS_INDEX_ID: str = "" # Static Index ID
    TWELVELABS_UPLOAD_TIMEOUT: int = 120  # seconds
    TWELVELABS_INDEX_TIMEOUT: int = 180  # seconds


    # Frontend Return URL
    FRONTEND_RETURN_URL: str = "http://localhost:3000/app/billing/return"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 15  # 15 × 2 instances = 30 (free tier limit)

    # Redis Streams (SSE replay buffer)
    # These are for "live-ish" updates only; DB remains the durable source of truth.
    REDIS_STREAM_TTL_S_CHAT: int = 60 * 60  # 1 hour
    REDIS_STREAM_TTL_S_SEARCH: int = 60 * 60  # 1 hour
    REDIS_STREAM_MAXLEN_CHAT: int = 10_000
    REDIS_STREAM_MAXLEN_SEARCH: int = 5_000
    REDIS_STREAM_MAXLEN_SEARCH_MORE: int = 5_000

    # Openrouter
    OPENAI_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_API_KEY: str = ""

    # LLM rate limits (per model, global across instances)
    # Provider hard-limits are per model; keys are derived from canonical `provider/resolved_name`.
    LLM_MODEL_GLOBAL_RPM: int = 1000
    LLM_MODEL_GLOBAL_TPM: int = 1_000_000
    LLM_MODEL_GLOBAL_RPD: int = 10_000
    # Must be >= worst-case estimated tokens for a single call, otherwise large calls can never pass.
    LLM_MODEL_GLOBAL_TPM_BURST: int = 200_000

    # Wait budgets for wait-and-retry smoothing.
    LLM_LIMIT_TIMEOUT_START_INTERACTIVE_S: float = 5.0
    LLM_LIMIT_TIMEOUT_TOKENS_INTERACTIVE_S: float = 5.0
    LLM_LIMIT_TIMEOUT_START_BACKGROUND_S: float = 30.0
    LLM_LIMIT_TIMEOUT_TOKENS_BACKGROUND_S: float = 30.0

    # Token estimation (fallback when callers don't provide max tokens).
    LLM_EST_COMPLETION_TOKENS_DEFAULT: int = 1024

    # OpenTelemetry
    OTEL_SERVICE_NAME: str = ""
    OTEL_RESOURCE_ATTRIBUTES: str = ""

    # Dodo Payments
    DODO_API_KEY: str = ""
    DODO_WEBHOOK_SECRET: str = ""
    DODO_BRAND_ID: str = ""
    DODO_ENVIRONMENT: str = "test_mode"  # or "live_mode"

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "lamrin@synthenova.xyz"

    # Whop Integration
    WHOP_API_KEY: str = ""
    WHOP_WEBHOOK_SECRET: str = ""
    WHOP_APP_ID: str = ""
    WHOP_PRODUCT_PRO: str = ""     # prod_XXX for Pro Research
    WHOP_PRODUCT_CREATOR: str = "" # prod_XXX for Creator Pass

    class Config:
        # Pydantic loads from the first file found in this list, OR merges them depending on library version.
        # But crucially, real Environment Variables (like from Secret Manager or Shell) ALWAYS override files.
        env_file = (".env", f".env.{os.getenv('APP_ENV', 'local')}")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
