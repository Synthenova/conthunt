"""Dodo Payments client wrapper with product caching."""
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from dodopayments import AsyncDodoPayments
from app.core import get_settings, logger

settings = get_settings()

# Global client instance
_client: Optional[AsyncDodoPayments] = None

# Product cache
_products_cache: dict = {}
_products_cache_expires: Optional[datetime] = None
CACHE_TTL_SECONDS = 300  # 5 minutes


def get_dodo_client() -> AsyncDodoPayments:
    """Get or create the Dodo client instance."""
    global _client
    if _client is None:
        _client = AsyncDodoPayments(
            bearer_token=settings.DODO_API_KEY,
            environment=settings.DODO_ENVIRONMENT,
            webhook_key=settings.DODO_WEBHOOK_SECRET,
        )
    return _client


async def get_products() -> list[dict]:
    """
    Fetch all subscription products for the brand with caching.
    Returns list of products with metadata containing app_role and credits.
    """
    global _products_cache, _products_cache_expires
    
    # Return cached if valid
    if _products_cache_expires and datetime.utcnow() < _products_cache_expires:
        return list(_products_cache.values())
    
    client = get_dodo_client()
    products = []
    
    try:
        # Fetch products - use items from response or async iterator
        response = await client.products.list(brand_id=settings.DODO_BRAND_ID)
        
        # Handle both paginated response (.items) and async iterator
        product_list = getattr(response, 'items', None) or response
                
        for product in product_list:
            if product.is_recurring:
                products.append({
                    "product_id": product.product_id,
                    "name": product.name,
                    "description": product.description or '',
                    "price": product.price or 0,
                    "currency": product.currency or 'USD',
                    "metadata": product.metadata or {},
                })
        
        # Update cache
        _products_cache = {p["product_id"]: p for p in products}
        _products_cache_expires = datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS)
        
        logger.info(f"Fetched {len(products)} Dodo products for brand {settings.DODO_BRAND_ID}")
        return products
        
    except Exception as e:
        logger.error(f"Failed to fetch Dodo products: {e}")
        # Return cached data if available, even if expired
        if _products_cache:
            logger.warning("Returning stale product cache")
            return list(_products_cache.values())
        raise


def get_product_by_id(product_id: str) -> Optional[dict]:
    """Get a product from cache by ID."""
    return _products_cache.get(product_id)


async def create_checkout_session(
    product_id: str,
    customer_id: Optional[str] = None,
    customer_email: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Create a checkout session for a product.
    Returns dict with session_id and url.
    """
    client = get_dodo_client()
    
    try:
        # Build customer object per Dodo SDK requirements
        # https://docs.dodopayments.com/developer-resources/checkout-session
        customer = None
        if customer_id:
            customer = {"customer_id": customer_id}
        elif customer_email:
            customer = {"email": customer_email}
        
        session = await client.checkout_sessions.create(
            product_cart=[{"product_id": product_id, "quantity": 1}],
            return_url=settings.FRONTEND_RETURN_URL,
            customer=customer,
            metadata=metadata,
        )
        
        logger.info(f"Created checkout session {session.session_id} for product {product_id}")
        return {
            "session_id": session.session_id,
            "url": session.checkout_url,
        }
        
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise


async def change_plan(
    subscription_id: str,
    product_id: str,
    proration_mode: str = "prorated_immediately",
) -> dict:
    """
    Change subscription plan immediately.
    Used for upgrades and applying pending downgrades.
    
    proration_mode options:
    - prorated_immediately: Fair billing based on remaining time
    - difference_immediately: Just the difference
    - full_immediately: Full new price
    """
    client = get_dodo_client()
    
    try:
        result = await client.subscriptions.change_plan(
            subscription_id,
            product_id=product_id,
            quantity=1,
            proration_billing_mode=proration_mode,
        )
        
        logger.info(f"Changed plan for subscription {subscription_id} to {product_id}")
        return {"success": True, "subscription": result}
        
    except Exception as e:
        logger.error(f"Failed to change plan for {subscription_id}: {e}")
        raise


async def preview_change_plan(
    subscription_id: str,
    product_id: str,
    proration_mode: str = "prorated_immediately",
) -> dict:
    """
    Preview plan change to show proration details before confirming.
    Returns immediate charge/credit info.
    """
    client = get_dodo_client()
    
    try:
        result = await client.subscriptions.preview_change_plan(
            subscription_id,
            product_id=product_id,
            quantity=1,
            proration_billing_mode=proration_mode,
        )
        
        # Extract key info from preview
        immediate_charge = getattr(result, 'immediate_charge', None)
        credit_amount = getattr(result, 'credit_amount', 0)
        charge_amount = getattr(result, 'charge_amount', 0)
        
        return {
            "immediate_charge": immediate_charge,
            "credit_amount": credit_amount,
            "charge_amount": charge_amount,
            "summary": getattr(immediate_charge, 'summary', None) if immediate_charge else None,
            "raw": result,
        }
        
    except Exception as e:
        logger.error(f"Failed to preview plan change for {subscription_id}: {e}")
        raise


async def set_cancel_at_period_end(subscription_id: str, cancel: bool = True) -> dict:
    """
    Set or unset cancel_at_next_billing_date flag.
    When set, subscription will expire at end of billing period.
    """
    client = get_dodo_client()
    
    try:
        result = await client.subscriptions.update(
            subscription_id,
            cancel_at_next_billing_date=cancel,
        )
        
        action = "scheduled cancellation" if cancel else "cancelled scheduled cancellation"
        logger.info(f"{action} for subscription {subscription_id}")
        return {"success": True, "subscription": result}
        
    except Exception as e:
        logger.error(f"Failed to update cancel_at_next_billing_date for {subscription_id}: {e}")
        raise


async def get_subscription(subscription_id: str) -> dict:
    """Retrieve subscription details from Dodo."""
    client = get_dodo_client()
    
    try:
        result = await client.subscriptions.retrieve(subscription_id)
        return {
            "subscription_id": result.subscription_id,
            "customer_id": result.customer_id,
            "product_id": result.product_id,
            "status": result.status,
            "cancel_at_period_end": result.cancel_at_period_end,
            "current_period_start": result.previous_billing_date,
            "current_period_end": result.next_billing_date,
        }
    except Exception as e:
        logger.error(f"Failed to get subscription {subscription_id}: {e}")
        raise
