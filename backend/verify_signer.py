
import sys
import os
from dotenv import load_dotenv
# Load local env so GCS_SIGNER_KEY_PATH is available when running from backend/
load_dotenv('.env.local')
# Assuming running from project root or backend dir
sys.path.append(os.getcwd())

# Import the REAL function, NO mocks
try:
    from app.services.cdn_signer import generate_signed_url
except ImportError:
    # If running from outside 'backend', try adding backend to path
    sys.path.append("backend")
    from app.services.cdn_signer import generate_signed_url

def test_generate_real_signed_url():
    # The user provided real URI
    uri = "gs://conthunt-dev-media/media/instagram/1571358031292093705/video/b36da8e1b8fc04f90592912775261343f1d9907c7236f493d888d7895bebb8e0.mp4"
    
    print(f"Generating signed URL for: {uri}")
    print("GCS_SIGNER_KEY_PATH:", os.environ.get("GCS_SIGNER_KEY_PATH"))
    try:
        url = generate_signed_url(uri)
        print("\n✅ SIGNED URL GENERATED SUCCESSFULLY:\n")
        print(url)
        print("\n(Copy and paste this URL into a browser to test access)\n")
    except Exception as e:
        print(f"\n❌ FAILED to generate signed URL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_real_signed_url()
