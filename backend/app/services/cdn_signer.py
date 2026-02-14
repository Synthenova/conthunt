import datetime
import asyncio
from collections.abc import Iterable

from google.cloud import storage
from google.oauth2 import service_account

from app.core import get_settings

_storage_client = None
_signer_creds = None
_signer_email = None


def _get_signer() -> tuple[service_account.Credentials, str]:
    global _signer_creds, _signer_email
    if _signer_creds is not None and _signer_email is not None:
        return _signer_creds, _signer_email

    s = get_settings()
    key_path = (s.GCS_SIGNER_KEY_PATH or "").strip()
    if not key_path:
        raise RuntimeError("Missing GCS_SIGNER_KEY_PATH (service account JSON key file path).")

    creds = service_account.Credentials.from_service_account_file(key_path)
    _signer_creds = creds
    _signer_email = creds.service_account_email
    return _signer_creds, _signer_email


def _get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        creds, _ = _get_signer()
        _storage_client = storage.Client(credentials=creds, project=creds.project_id)
    return _storage_client


def generate_signed_url(gcs_filename: str, expiration_seconds: int = 3600) -> str:
    """
    Generate a V4 signed URL for a GCS object using ONLY a local service account key.
    """
    path = gcs_filename
    if path.startswith("gs://"):
        path = path[5:]  # remove gs://

    if "/" not in path:
        raise ValueError(f"Invalid GCS URI: {gcs_filename}. Must be gs://bucket/path")

    bucket_name, blob_name = path.split("/", 1)

    creds, sa_email = _get_signer()
    client = _get_storage_client()
    blob = client.bucket(bucket_name).blob(blob_name)

    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(seconds=expiration_seconds),
        method="GET",
        credentials=creds,
        service_account_email=sa_email,
    )


def should_sign_asset(asset: dict) -> bool:
    return bool(asset.get("gcs_uri")) and asset.get("status") in ("stored", "downloaded")


async def bulk_sign_gcs_uris(
    gcs_uris: Iterable[str],
    expiration_seconds: int = 3600,
    max_concurrency: int = 25,
) -> dict[str, str]:
    """
    Sign a set of GCS URIs. Uses asyncio.to_thread to avoid blocking the event loop when
    signing lots of URLs inside async endpoints.
    """
    unique = {u for u in gcs_uris if u}
    if not unique:
        return {}

    sem = asyncio.Semaphore(max_concurrency)
    signed: dict[str, str] = {}

    async def one(uri: str) -> None:
        if uri in signed:
            return
        async with sem:
            signed[uri] = await asyncio.to_thread(generate_signed_url, uri, expiration_seconds)

    await asyncio.gather(*(one(u) for u in unique))
    return signed
