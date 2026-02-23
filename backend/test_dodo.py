import asyncio
from app.services.dodo_client import get_dodo_client

async def update_payment_fallback(subscription_id: str, return_url: str):
    client = get_dodo_client()
    try:
        result = await client.subscriptions.update_payment_method(
            subscription_id,
            type="new",
            return_url=return_url,
        )
        print("Success:", getattr(result, 'payment_link', None))
    except Exception as e:
        err_msg = str(e)
        print("Failed update_payment_method. Error:", err_msg)
        if "422" in err_msg or "INVALID_REQUEST_PARAMETERS" in err_msg or "cannot recreate invoice" in err_msg:
            print("Falling back to customer portal...")
            sub = await client.subscriptions.retrieve(subscription_id)
            session = await client.customers.customer_portal.create(customer_id=sub.customer.customer_id)
            portal_link = getattr(session, 'link', None)
            if not portal_link and isinstance(session, dict):
                portal_link = session.get('link')
            print("Fallback portal link:", portal_link)
        else:
            raise

async def main():
    await update_payment_fallback('sub_0NW3ePkCfi8n5s70eeYBL', 'https://example.com')

if __name__ == "__main__":
    asyncio.run(main())
