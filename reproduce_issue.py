
import hmac
import hashlib
import base64
import time

def generate_signed_url_mock(
    key_val: str,
    key_name: str,
    url_prefix: str,
    gcs_filename: str,
    expiration_seconds: int = 3600
):
    # Logic from cdn_signer.py
    
    if gcs_filename.startswith("gs://"):
        parts = gcs_filename.replace("gs://", "").split("/", 1)
        if len(parts) > 1:
            gcs_filename = parts[1]
            
    if gcs_filename.startswith("/"):
        gcs_filename = gcs_filename[1:]

    if not url_prefix.endswith("/"):
        url_prefix += "/"
        
    base_url = f"{url_prefix}{gcs_filename}"
    
    # Mock expiration to a fixed time for reproducibility if needed, but not strictly required for padding check
    # using strict time here to match what we might want to check
    expiration_time = 1766145432 # content from user request URL
    
    url_to_sign = f"{base_url}?Expires={expiration_time}&KeyName={key_name}"
    
    print(f"URL to sign: {url_to_sign}")
    
    try:
        key_bytes = base64.urlsafe_b64decode(key_val)
        print("Key bytes decoded successfully", key_bytes)
    except Exception:
        key_bytes = key_val.encode('utf-8')

    signature = hmac.new(
        key_bytes,
        url_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8')
    print("Signed URL", f"{url_to_sign}&Signature={encoded_signature}")
    print(f"Generated Signature: {encoded_signature}")
    
    if "=" in encoded_signature:
        print("FAIL: Signature contains padding '='. Cloud CDN requires no padding.")
    else:
        print("SUCCESS: Signature does not contain padding.")

if __name__ == "__main__":
    # Test with a dummy key (base64 encoded 16 bytes)
    # 16 bytes = 22 chars in base64 with padding
    dummy_key = "a" * 22 + "==" 
    # Or just random bytes
    import os
    random_key_bytes = os.urandom(16)
    dummy_key = base64.urlsafe_b64encode(random_key_bytes).decode('utf-8')
    key_bytes = base64.urlsafe_b64decode("8TyZjnptTyUN6tWRidU-4g==")
    print(key_bytes)
    print("Testing with random key...")
    generate_signed_url_mock(
        key_val="8TyZjnptTyUN6tWRidU-4g==",
        key_name="conthunt-backend-bucket-lb-signingkey",
        url_prefix="http://34.160.106.248/",
        gcs_filename="media/youtube/QnzzPBudpLs/thumbnail/19c42b0b4097f2e5743d431fea52dc07b4521ad5786e7c6b4e362e619df3300e.jpg"
    )
