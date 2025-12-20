import hmac
import hashlib
import base64
import time
from app.core import settings

def generate_signed_url(
    gcs_filename: str,
    expiration_seconds: int = 3600
) -> str:
    """
    Generates a full URL with a Cloud CDN V1 signature.
    
    Args:
        gcs_filename: The relative path to the file (e.g. "videos/reel_1.mp4")
                     or the full object name.
    """
    conf = settings.get_settings()
    
    # --- 1. Clean Path Logic ---
    # Removes gs://, bucket names, and leading slashes
    path = gcs_filename
    if path.startswith("gs://"):
        path = path.split("/", 3)[-1]
    path = path.lstrip("/") 

    # --- 2. Base URL ---
    url_prefix = conf.CDN_URL_PREFIX.rstrip("/")
    base_url = f"{url_prefix}/{path}"
    
    # --- 3. Prepare Key (THE CRITICAL FIX) ---
    key_val = conf.CDN_SIGNING_KEY_VALUE
    
    # Fix Padding: Ensure the key string is a multiple of 4 for the decoder
    missing_padding = len(key_val) % 4
    if missing_padding:
        key_val += '=' * (4 - missing_padding)
    
    try:
        # DECODE the string to get the actual 16 secret bytes
        key_bytes = base64.urlsafe_b64decode(key_val)
    except Exception as e:
        # If this fails, the key in your .env is wrong. Do not proceed.
        raise ValueError(f"CRITICAL: Key decoding failed. Check .env file. Details: {e}")

    # --- 4. Sign ---
    expiration_time = int(time.time()) + expiration_seconds
    key_name = conf.CDN_SIGNING_KEY_NAME
    
    url_to_sign = f"{base_url}?Expires={expiration_time}&KeyName={key_name}"
    
    signature = hmac.new(
        key_bytes,
        url_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    # --- 5. Format Signature ---
    # Google wants URL-safe base64, with NO padding (=) at the end
    encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip("=")
    
    return f"{url_to_sign}&Signature={encoded_signature}"
