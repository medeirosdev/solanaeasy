"""
SolanaEasy -- Quick Start Example

This is the simplest possible integration. It creates a payment session,
prints the deposit address, and waits for the customer to pay.

Prerequisites:
    pip install solanaeasy
    export SOLANAEASY_API_KEY=sk_test_1234567890

Usage:
    python quickstart.py
"""

from solanaeasy import SolanaEasy
from solanaeasy.exceptions import WaitTimeout

sdk = SolanaEasy(
    api_key="sk_test_1234567890",
    base_url="http://localhost:8000",
)

# 1. Create a payment session
session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="order_001",
    description="Nike Air Max Pulse",
)

print(f"Session created:  {session.session_id}")
print(f"Deposit address:  {session.wallet_public_key}")
print(f"Payment URL:      {session.payment_url}")
print(f"Expires at:       {session.expires_at}")
print()

# 2. Wait for the customer to deposit funds
print("Waiting for payment...")
try:
    status = sdk.wait_for_confirmation(
        session.session_id,
        timeout=300,
        on_update=lambda s: print(f"  State changed: {s.state} -- {s.human_message}"),
    )
    print()
    print(f"Payment {status.state}!")
    print(f"Message: {status.human_message}")
except WaitTimeout as e:
    print(f"Timed out after {e.timeout}s. Last state: {e.last_status.state}")
