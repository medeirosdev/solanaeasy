# FastAPI Integration

Complete guide to integrating SolanaEasy with a FastAPI application.

## Full Example

```python title="main.py"
from fastapi import FastAPI, Request, Response
from solanaeasy import AsyncSolanaEasy

app = FastAPI(title="My Store")

sdk = AsyncSolanaEasy(
    api_key="sk_test_1234567890",
    base_url="http://localhost:8000",
    webhook_secret="whsec_test_secret",
)


# ── Webhook Handlers ──────────────────────────────────────────────

@sdk.on("payment.confirmed")
async def on_confirmed(event):
    """Called when a payment is confirmed on-chain."""
    print(f"✓ Order paid! Session: {event.session_id}")
    # Mark order as paid in your database
    # Send confirmation email
    # Unlock digital content

@sdk.on("payment.failed")
async def on_failed(event):
    """Called when a payment fails."""
    print(f"✗ Payment failed: {event.data.human_message}")
    # Notify customer

@sdk.on("payment.expired")
async def on_expired(event):
    """Called when a session expires."""
    # Release reserved inventory


# ── API Endpoints ─────────────────────────────────────────────────

@app.post("/api/checkout")
async def create_checkout(amount: float = 150.00, product: str = "Premium"):
    """Create a payment session and return the deposit address."""
    session = await sdk.create_payment(
        amount=amount,
        order_id=f"web_{id(session)}",
        description=product,
        metadata={"source": "web"},
    )
    return {
        "session_id": session.session_id,
        "payment_url": session.payment_url,
        "wallet": session.wallet_public_key,
        "amount": session.amount,
    }

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Check the current payment status."""
    status = await sdk.check_status(session_id)
    return {
        "state": status.state,
        "message": status.human_message,
        "tx_hash": status.tx_hash,
    }

@app.post("/api/refund/{session_id}")
async def refund_payment(session_id: str):
    """Refund a confirmed payment."""
    status = await sdk.refund(session_id)
    return {"state": status.state, "message": status.human_message}

@app.post("/webhook/solana")
async def webhook_endpoint(request: Request):
    """Receive webhook events from SolanaEasy."""
    payload = await request.body()
    signature = request.headers.get("X-SolanaEasy-Signature", "")
    try:
        event = await sdk.process_webhook(payload=payload, signature=signature)
        return {"received": True, "event_type": event.event_type}
    except Exception as e:
        return Response(content=str(e), status_code=400)
```

## Running

```bash
uvicorn main:app --reload --port 9000
```

## Testing

```bash
# Create a payment
curl -X POST http://localhost:9000/api/checkout

# Check status
curl http://localhost:9000/api/status/sess_abc123
```
