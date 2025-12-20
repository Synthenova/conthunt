
import sys
import os
import base64

# Add the backend directory to sys.path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.cdn_signer import generate_signed_url
from app.core import settings

def verify_fix():
    print("Verifying fix in cdn_signer.py...")
    
    # 1. Check if we can generate a URL without error
    try:
        url = generate_signed_url(
            gcs_filename="media/test.mp4",
            expiration_seconds=3600
        )
        print(f"Generated URL: {url}")
        
        # 2. Check for padding
        if "Signature=" in url:
            signature = url.split("Signature=")[1]
            if "=" in signature:
                print("FAIL: Signature still contains padding '='.")
                sys.exit(1)
            else:
                print("SUCCESS: Signature does not contain padding.")
        else:
            print("FAIL: URL does not contain Signature.")
            sys.exit(1)
            
    except Exception as e:
        print(f"FAIL: valid generation failed with error: {e}")
        # If it fails due to key decoding (which we added), it means .env is wrong, 
        # which is also a useful result to verify "Verify Settings".
        sys.exit(1)

if __name__ == "__main__":
    verify_fix()
