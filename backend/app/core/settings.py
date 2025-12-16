"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_SCHEMA: str = "conthunt"

    # GCP / Firebase
    GCLOUD_PROJECT: str = "conthunt-dev"
    GCP_PROJECT: str = "conthunt-dev"

    # ScrapeCreators API
    SCRAPECREATORS_API_KEY: str
    SCRAPECREATORS_BASE_URL: str = "https://api.scrapecreators.com"

    # GCS Buckets
    GCS_BUCKET_RAW: str = "conthunt-dev-raw"
    GCS_BUCKET_MEDIA: str = "conthunt-dev-media"

    # Media download behavior
    MEDIA_DOWNLOAD_ENABLED: bool = True
    MEDIA_MAX_CONCURRENCY: int = 4
    MEDIA_HTTP_TIMEOUT_S: int = 40
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
    LANGGRAPH_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
