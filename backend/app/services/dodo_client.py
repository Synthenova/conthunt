"""Dodo Payments API client."""
import httpx
from app.core.settings import get_settings
from app.core import logger


class DodoClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.DODO_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.DODO_API_KEY}",
            "Content-Type": "application/json",
        }

    async def create_checkout_session(self, *, product_id: str, firebase_uid: str) -> dict:
        """Create a hosted checkout session."""
        settings = get_settings()
        payload = {
            "product_cart": [{"product_id": product_id, "quantity": 1}],
            "return_url": settings.FRONTEND_RETURN_URL,
            "metadata": {
                "firebase_uid": firebase_uid,
            },
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/checkouts", 
                    headers=self.headers, 
                    json=payload
                )
                r.raise_for_status()
                return r.json()
            except Exception as e:
                logger.error(f"Dodo create_checkout_session failed: {e}")
                if isinstance(e, httpx.HTTPStatusError):
                    logger.error(f"Response: {e.response.text}")
                raise

    async def change_plan(
        self, 
        *, 
        subscription_id: str, 
        new_product_id: str, 
        proration_billing_mode: str = "prorated_immediately"
    ) -> dict:
        """Change subscription plan."""
        payload = {
            "product_id": new_product_id,
            "quantity": 1,
            "proration_billing_mode": proration_billing_mode,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/subscriptions/{subscription_id}/change-plan",
                    headers=self.headers,
                    json=payload,
                )
                r.raise_for_status()
                return r.json()
            except Exception as e:
                logger.error(f"Dodo change_plan failed: {e}")
                if isinstance(e, httpx.HTTPStatusError):
                    logger.error(f"Response: {e.response.text}")
                raise

# Global client instance
dodo_client = DodoClient()
