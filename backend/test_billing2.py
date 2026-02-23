import asyncio
import json
from app.api.v1.billing import get_subscription

async def test():
    class DummyUser(dict):
        def get(self, key, default=None):
            return super().get(key, default)
            
    # Mock billing_service
    import sys
    from unittest.mock import AsyncMock
    import app.api.v1.billing as billing
    billing.billing_service.get_user_subscription = AsyncMock(return_value={
        "subscription_id": "sub_123",
        "product_id": "prod_1",
        "status": "cancelled",
        "cancel_at_period_end": True
    })
    
    user = DummyUser({"db_user_id": "user_123", "role": "pro"})
    res = await get_subscription(user)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
