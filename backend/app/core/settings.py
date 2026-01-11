"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_SCHEMA: str = "conthunt"
    LOG_LEVEL: str = "DEBUG"

    # GCP / Firebase
    GCLOUD_PROJECT: str = "conthunt-dev"
    GCP_PROJECT: str = "conthunt-dev"
    GCP_REGION: str = "us-central1"
    
    # Cloud Tasks
    CLOUD_TASKS_SA_EMAIL: str = "tasks-invoker@conthunt-dev.iam.gserviceaccount.com"
    API_BASE_URL: str = "https://api.conthunt.com"
    
    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # queues
    QUEUE_MEDIA_DOWNLOAD: str = "media-download-queue"
    QUEUE_TWELVELABS: str = "twelvelabs-queue"
    QUEUE_GEMINI: str = "gemini-queue"
    QUEUE_RAW_ARCHIVE: str = "raw-archive-queue"
    QUEUE_MEDIA_DOWNLOAD_PRIORITY: str = "media-download-priority"


    # ScrapeCreators API
    SCRAPECREATORS_API_KEY: str
    SCRAPECREATORS_BASE_URL: str = "https://api.scrapecreators.com"

    # GCS Buckets
    GCS_BUCKET_RAW: str = "conthunt-dev-raw"
    GCS_BUCKET_MEDIA: str = "conthunt-dev-media"

    # Cloud CDN
    CDN_SIGNING_KEY_NAME: str = "my-cdn-signing-key"
    CDN_SIGNING_KEY_VALUE: str = ""
    CDN_URL_PREFIX: str = "http://34.120.120.120/" # Placeholder, user must set in env

    # Media download behavior
    MEDIA_DOWNLOAD_ENABLED: bool = True
    MEDIA_MAX_CONCURRENCY: int = 4
    MEDIA_HTTP_TIMEOUT_S: int = 60
    RAW_UPLOAD_ENABLED: bool = True

    # TwelveLabs Video Analysis
    TWELVELABS_API_KEY: str = ""
    TWELVELABS_INDEX_ID: str = "" # Static Index ID
    TWELVELABS_DEFAULT_INDEX_NAME: str = "conthunt-videos"
    TWELVELABS_UPLOAD_TIMEOUT: int = 120  # seconds
    TWELVELABS_INDEX_TIMEOUT: int = 180  # seconds

    # Dodo Payments
    DODO_API_KEY: str = ""
    DODO_WEBHOOK_SECRET: str = ""
    DODO_BASE_URL: str = "https://test.dodopayments.com"

    # Products
    DODO_PRODUCT_CREATOR: str = "pdt_ak5GBsLOOR8y7tqEh2plw"
    DODO_PRODUCT_PRO: str = "pdt_dPXYTaQF4iax5DT7PLD8A"

    # Frontend Return URL
    FRONTEND_RETURN_URL: str = "http://localhost:3000/app/billing/return"

    # LangGraph & Redis
    # LANGGRAPH_URL is no longer required - we use direct graph calls now
    LANGGRAPH_URL: str = ""  # Deprecated - kept for backward compatibility
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
