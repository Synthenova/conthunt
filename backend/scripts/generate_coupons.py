import os
from pathlib import Path
from dotenv import load_dotenv
from dodopayments import DodoPayments

# Load environment variables from .env.local
env_path = Path(__file__).resolve().parent.parent / ".env.prod"
load_dotenv(env_path)

def create_single_use_100pct_coupon(client: DodoPayments, product_id: str, code: str):
    """
    Creates a single-use 100% off discount code restricted to a given product.
    
    Notes (per Dodo docs):
    - type="percentage" -> amount is in basis points, so 100% = 10000
    - usage_limit=1 -> single use
    - restricted_to=[product_id] -> applies only to that product
    """
    discount = client.discounts.create(
        name=code,                    # Use the code as the name
        code=code,                    # The actual redeemable code
        type="percentage",
        amount=10000,                 # 100.00%
        usage_limit=1,                # single use
        restricted_to=[product_id],   # only this product
    )
    return discount

if __name__ == "__main__":
    api_key = os.environ.get("DODO_PAYMENTS_API_KEY") or os.environ.get("DODO_API_KEY")

    if not api_key:
        print("Error: DODO_PAYMENTS_API_KEY or DODO_API_KEY not found in environment variables.")
        exit(1)

    client = DodoPayments(
        bearer_token=api_key,
        # environment="test_mode",  # uncomment if your SDK supports it and you want test mode
    )

    product_id = "pdt_0NW4iNZT4XPaZgDYq9JKQ"
    
    # List of codes to generate
    import random
    import string

    def generate_random_code(length=8):
        return ''.join(random.choices(string.ascii_uppercase, k=length))

    codes = [generate_random_code() for _ in range(25)]

    print(f"Generating {len(codes)} random coupons for product {product_id}...")

    for code in codes:
        try:
            discount = create_single_use_100pct_coupon(client, product_id, code)
            print(discount.code)
        except Exception as e:
            print(f"Failed to create discount {code}: {e}")
