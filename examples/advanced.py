"""
SolanaEasy -- Advanced Features Example

Demonstrates refund, cancel, receipt, wallet balance, and metadata.

Prerequisites:
    pip install solanaeasy
    export SOLANAEASY_API_KEY=sk_test_1234567890

Usage:
    python advanced.py
"""

from solanaeasy import SolanaEasy
from solanaeasy.exceptions import SolanaEasyError

sdk = SolanaEasy(
    api_key="sk_test_1234567890",
    base_url="http://localhost:8000",
)


def demo_metadata():
    """Create a payment with custom metadata attached."""
    print("=== Metadata ===")
    session = sdk.create_payment(
        amount=99.90,
        order_id="order_meta_001",
        description="Keychron Q1 Pro Keyboard",
        metadata={
            "user_id": "u_42",
            "sku": "KEYCHRON-Q1-PRO",
            "discount_code": "HACKATHON10",
        },
    )
    print(f"Session: {session.session_id}")
    print(f"Metadata: {session.metadata}")
    print()
    return session


def demo_wallet_balance(session_id: str):
    """Check the real-time SOL balance of a session's wallet."""
    print("=== Wallet Balance ===")
    info = sdk.get_wallet_balance(session_id)
    print(f"Wallet:  {info['wallet_public_key']}")
    print(f"Balance: {info['sol_balance']} SOL")
    print(f"Network: {info['network']}")
    print()


def demo_cancel(session_id: str):
    """Cancel a session before the customer pays."""
    print("=== Cancel Session ===")
    status = sdk.cancel_session(session_id)
    print(f"State: {status.state}")
    print(f"Message: {status.human_message}")
    print()


def demo_list_payments():
    """List all payments with optional filtering."""
    print("=== List Payments ===")
    payments = sdk.list_payments(limit=5)
    for p in payments:
        print(f"  {p.session_id}  {p.amount} {p.currency}  [{p.state}]")
    print()


if __name__ == "__main__":
    # 1. Create with metadata
    session = demo_metadata()

    # 2. Check wallet balance
    demo_wallet_balance(session.session_id)

    # 3. Cancel the session (since we won't pay in this demo)
    demo_cancel(session.session_id)

    # 4. List all payments
    demo_list_payments()

    print("Done! For refund and receipt examples, first confirm a payment")
    print("using the quickstart.py example, then run:")
    print()
    print("  receipt = sdk.get_receipt('sess_...')")
    print("  refund  = sdk.refund('sess_...')")
