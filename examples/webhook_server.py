"""
SolanaEasy -- FastAPI Webhook Integration Example

Shows how to receive real-time payment events via webhooks
using FastAPI and the async SDK.

Prerequisites:
    pip install solanaeasy fastapi uvicorn
    export SOLANAEASY_API_KEY=sk_test_1234567890
    export SOLANAEASY_WEBHOOK_SECRET=whsec_test_secret

Usage:
    uvicorn webhook_server:app --port 9000
"""

from fastapi import FastAPI, Request, Response
from solanaeasy import AsyncSolanaEasy

app = FastAPI(title="My Store Webhook Server")

sdk = AsyncSolanaEasy(
    api_key="sk_test_1234567890",
    base_url="http://localhost:8000",
    webhook_secret="whsec_test_secret",
)


# Register event handlers using the decorator pattern
@sdk.on("payment.confirmed")
async def handle_confirmed(event):
    """Called automatically when a payment is confirmed on-chain."""
    print(f"[CONFIRMED] Order paid! Session: {event.session_id}")
    print(f"  Message: {event.data.human_message}")
    # Here you would:
    # - Mark the order as paid in your database
    # - Send a confirmation email
    # - Unlock digital content


@sdk.on("payment.failed")
async def handle_failed(event):
    """Called when a payment fails (insufficient funds, network error, etc.)."""
    print(f"[FAILED] Payment failed for session: {event.session_id}")
    print(f"  Reason: {event.data.human_message}")
    # Here you would notify the customer


@sdk.on("payment.expired")
async def handle_expired(event):
    """Called when a payment session expires without being paid."""
    print(f"[EXPIRED] Session expired: {event.session_id}")
    # Here you would release reserved inventory


@app.post("/webhook/solana")
async def webhook_endpoint(request: Request):
    """
    Receives webhook events from SolanaEasy.
    The SDK handles signature verification and event dispatching.
    """
    payload = await request.body()
    signature = request.headers.get("X-SolanaEasy-Signature", "")

    try:
        event = await sdk.process_webhook(payload=payload, signature=signature)
        return {"received": True, "event_type": event.event_type}
    except Exception as e:
        return Response(content=str(e), status_code=400)


@app.post("/create-checkout")
async def create_checkout():
    """Example endpoint that creates a payment session."""
    session = await sdk.create_payment(
        amount=150.00,
        order_id="order_web_001",
        description="Nike Air Max Pulse",
        metadata={"source": "web", "user_id": "u_42"},
    )
    return {
        "session_id": session.session_id,
        "payment_url": session.payment_url,
        "wallet": session.wallet_public_key,
    }
