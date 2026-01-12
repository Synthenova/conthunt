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

    # =========================================================================
    # Product Caching (for dynamic product → role mapping)
    # =========================================================================

    async def list_products(self, recurring_only: bool = True) -> list[dict]:
        """
        List all products from Dodo API.
        
        Args:
            recurring_only: If True, filter to subscription products only
            
        Returns:
            List of product dicts with product_id, name, is_recurring, price, 
            billing_interval (monthly/yearly), and metadata.
        """
        products = []
        try:
            async with get_dodo_client() as client:
                async for prod in client.products.list():
                    prod_dict = prod.model_dump() if hasattr(prod, "model_dump") else dict(prod)
                    
                    is_recurring = prod_dict.get("is_recurring", False)
                    if recurring_only and not is_recurring:
                        continue
                    
                    # Extract billing interval from Dodo's payment_frequency_count/interval
                    # or from the product structure
                    payment_freq = prod_dict.get("payment_frequency_count", 1)
                    payment_interval = prod_dict.get("payment_frequency_interval", "month")
                    
                    # Determine billing_interval: monthly vs yearly
                    if payment_interval == "year" or payment_freq >= 12:
                        billing_interval = "yearly"
                    else:
                        billing_interval = "monthly"
                    
                    metadata = prod_dict.get("metadata") or {}
                    
                    products.append({
                        "product_id": prod_dict.get("product_id"),
                        "name": prod_dict.get("name"),
                        "is_recurring": is_recurring,
                        "price": prod_dict.get("price"),
                        "currency": prod_dict.get("currency"),
                        "billing_interval": billing_interval,
                        "app_role": metadata.get("app_role"),
                        "metadata": metadata,
                        "updated_at": prod_dict.get("updated_at"),
                        "raw": prod_dict,
                    })
            
            logger.info(f"Listed {len(products)} products from Dodo")
            return products
        except Exception as e:
            logger.error(f"Failed to list products: {e}")
            raise

    async def get_products_for_checkout(self) -> list[dict]:
        """
        Get all subscription products formatted for checkout/frontend display.
        Filters to only products that have app_role in metadata.
        """
        products = await self.list_products(recurring_only=True)
        
        # Filter to products with valid app_role
        valid_products = [
            p for p in products 
            if p.get("app_role") in ("creator", "pro_research")
        ]
        
        # Sort by role then by interval (monthly first)
        valid_products.sort(key=lambda p: (
            0 if p["app_role"] == "creator" else 1,
            0 if p["billing_interval"] == "monthly" else 1
        ))
        
        return valid_products

    async def get_product_by_role_and_interval(
        self, 
        app_role: str, 
        billing_interval: str = "monthly"
    ) -> dict | None:
        """
        Get a specific product by app_role and billing_interval.
        
        Args:
            app_role: "creator" or "pro_research"
            billing_interval: "monthly" or "yearly"
            
        Returns:
            Product dict or None if not found
        """
        products = await self.list_products(recurring_only=True)
        
        for p in products:
            if p.get("app_role") == app_role and p.get("billing_interval") == billing_interval:
                return p
        
        # Fallback: try to find any product with matching role
        for p in products:
            if p.get("app_role") == app_role:
                logger.warning(f"No exact match for {app_role}/{billing_interval}, using {p['product_id']}")
                return p
        
        return None

    async def get_product(self, product_id: str) -> dict | None:
        """
        Fetch a single product from Dodo API.
        
        Args:
            product_id: Dodo product ID
            
        Returns:
            Product dict or None if not found
        """
        try:
            async with get_dodo_client() as client:
                prod = await client.products.retrieve(product_id)
                prod_dict = prod.model_dump() if hasattr(prod, "model_dump") else dict(prod)
                
                return {
                    "product_id": prod_dict.get("product_id"),
                    "name": prod_dict.get("name"),
                    "is_recurring": prod_dict.get("is_recurring", False),
                    "price": prod_dict.get("price"),
                    "currency": prod_dict.get("currency"),
                    "metadata": prod_dict.get("metadata") or {},
                    "updated_at": prod_dict.get("updated_at"),
                    "raw": prod_dict,
                }
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None

    async def ensure_product_cached(self, conn, product_id: str) -> None:
        """
        Ensure product exists in local cache (dodo_products table).
        If not, fetch from Dodo API and cache it.
        
        Args:
            conn: AsyncConnection to use
            product_id: Dodo product ID
        """
        from app.db.queries.billing import product_exists, upsert_product
        
        # Check if already cached
        if await product_exists(conn, product_id):
            return
        
        # Fetch from Dodo API
        product = await self.get_product(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found in Dodo API, cannot cache")
            return
        
        # Cache it
        await upsert_product(
            conn,
            product_id=product["product_id"],
            name=product["name"],
            is_recurring=product["is_recurring"],
            price=product["price"],
            currency=product["currency"],
            metadata=product["metadata"],
            raw=product["raw"],
        )
        logger.info(f"Cached product {product_id} from Dodo API")


# Global instance
dodo_service = DodoService()

