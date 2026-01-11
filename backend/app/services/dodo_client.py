"""Dodo Payments client using official SDK."""
from uuid import UUID
from dodopayments import AsyncDodoPayments
from app.core.settings import get_settings
from app.core import logger


def get_dodo_client() -> AsyncDodoPayments:
    """Get configured async Dodo client."""
    settings = get_settings()
    environment = "test_mode" if "test" in settings.DODO_BASE_URL else "live_mode"
    
    return AsyncDodoPayments(
        bearer_token=settings.DODO_API_KEY,
        environment=environment,
        timeout=30.0,
    )


class DodoService:
    """High-level Dodo operations."""

    async def create_checkout_session(
        self,
        *,
        product_id: str,
        user_id: UUID,  # Internal DB user ID
        customer_id: str | None = None,
        return_url: str | None = None
    ) -> dict:
        """
        Create checkout session.
        
        Args:
            product_id: Dodo product ID
            user_id: Internal DB user UUID (stored in metadata for webhooks)
            customer_id: Dodo customer ID (if user already has one)
            return_url: Where to redirect after checkout
        """
        settings = get_settings()
        
        try:
            async with get_dodo_client() as client:
                kwargs = {
                    "product_cart": [{"product_id": product_id, "quantity": 1}],
                    "return_url": return_url or settings.FRONTEND_RETURN_URL,
                    "metadata": {"user_id": str(user_id)},
                }
                
                if customer_id:
                    kwargs["customer"] = {"customer_id": customer_id}
                
                logger.info(f"Creating checkout session: {kwargs}")
                session = await client.checkout_sessions.create(**kwargs)
                logger.info(f"Checkout session created. Attributes: {dir(session)}")
                
                # Check for possible URL attributes
                url = getattr(session, 'url', None) or getattr(session, 'checkout_url', None) or getattr(session, 'payment_link', None)
                
                if not url:
                    logger.error(f"Could not find URL in session object: {session}")
                    raise ValueError("No checkout URL in response")

                return {
                    "checkout_url": url,
                    "session_id": session.session_id,
                }
        except Exception as e:
            logger.error(f"Dodo checkout failed: {e}")
            raise

    async def get_subscription(self, subscription_id: str) -> dict | None:
        """Fetch subscription from Dodo API."""
        if not subscription_id:
            return None
            
        try:
            async with get_dodo_client() as client:
                sub = await client.subscriptions.retrieve(subscription_id)
                return {
                    "subscription_id": sub.subscription_id,
                    "status": sub.status,
                    "product_id": sub.product_id,
                    "current_period_start": getattr(sub, 'current_period_start', None),
                    "current_period_end": getattr(sub, 'current_period_end', None),
                    "next_billing_date": getattr(sub, 'next_billing_date', None),
                    "cancel_at_period_end": getattr(sub, 'cancel_at_period_end', False),
                }
        except Exception as e:
            logger.error(f"Failed to fetch subscription {subscription_id}: {e}")
            return None

    async def get_customer(self, customer_id: str) -> dict | None:
        """Fetch customer from Dodo API."""
        if not customer_id:
            return None
            
        try:
            async with get_dodo_client() as client:
                cust = await client.customers.retrieve(customer_id)
                return {
                    "customer_id": cust.customer_id,
                    "email": cust.email,
                    "name": cust.name,
                }
        except Exception as e:
            logger.error(f"Failed to fetch customer {customer_id}: {e}")
            return None

    async def change_plan(
        self,
        *,
        subscription_id: str,
        new_product_id: str,
        proration_mode: str = "prorated_immediately"
    ) -> dict:
        """Change subscription plan."""
        async with get_dodo_client() as client:
            result = await client.subscriptions.change_plan(
                subscription_id,
                product_id=new_product_id,
                quantity=1,
                proration_billing_mode=proration_mode,
            )
            return {
                "subscription_id": result.subscription_id,
                "status": result.status,
            }

    async def cancel_subscription(
        self,
        subscription_id: str,
        immediate: bool = False
    ) -> dict:
        """Cancel subscription (at period end by default)."""
        async with get_dodo_client() as client:
            result = await client.subscriptions.update(
                subscription_id,
                cancel_at_period_end=not immediate,
            )
            return {"status": "cancelled" if immediate else "cancel_scheduled"}


# Global instance
dodo_service = DodoService()
