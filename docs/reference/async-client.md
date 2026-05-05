# AsyncSolanaEasy (Async Client)

Asynchronous version of the SDK client. Identical interface to [`SolanaEasy`](client.md), but all methods return coroutines.

Ideal for **FastAPI**, **aiohttp**, and any `asyncio`-based application.

## Constructor

```python
from solanaeasy import AsyncSolanaEasy

sdk = AsyncSolanaEasy(
    api_key="sk_test_...",
    network="devnet",
    base_url="http://localhost:8000",
    timeout=30.0,
    webhook_secret="whsec_...",
)
```

Parameters are identical to [`SolanaEasy`](client.md#constructor).

## Async Context Manager

The recommended pattern:

```python
async with AsyncSolanaEasy(api_key="sk_test_...") as sdk:
    session = await sdk.create_payment(
        amount=50.00,
        order_id="order_123",
    )
    status = await sdk.wait_for_confirmation(session.session_id)
```

## Methods

All methods are identical to `SolanaEasy` but use `async/await`:

### Payment Methods

```python
# Create a payment
session = await sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    metadata={"user_id": "u_42"},
)

# Check status
status = await sdk.check_status(session.session_id)

# Wait for confirmation (uses asyncio.sleep internally)
status = await sdk.wait_for_confirmation(
    session.session_id,
    timeout=120,
    on_update=lambda s: print(s.state),  # Can be sync or async
)

# List payments
payments = await sdk.list_payments(status="CONFIRMED")

# Cancel
status = await sdk.cancel_session(session.session_id)

# Refund
status = await sdk.refund(session.session_id)

# Receipt
receipt = await sdk.get_receipt(session.session_id)

# Wallet balance
info = await sdk.get_wallet_balance(session.session_id)
```

### Webhook Methods

```python
# Register webhook
await sdk.register_webhook(url="https://yoursite.com/webhook")

# Process webhook (dispatches async handlers)
event = await sdk.process_webhook(payload=body, signature=sig)

# Verify only (synchronous — no I/O needed)
event = sdk.verify_webhook_signature(payload=body, signature=sig)
```

### Async Event Handlers

The `@sdk.on()` decorator supports both sync and async handlers:

```python
@sdk.on("payment.confirmed")
async def handle_confirmed(event):
    await update_database(event.session_id)
    await send_email(event.session_id)

@sdk.on("payment.failed")
def handle_failed(event):  # sync is fine too
    log_failure(event.session_id)
```

## Key Differences from SolanaEasy

| Feature | `SolanaEasy` | `AsyncSolanaEasy` |
|---|---|---|
| Sleep method | `time.sleep()` | `asyncio.sleep()` |
| HTTP client | `httpx.Client` | `httpx.AsyncClient` |
| Context manager | `with` | `async with` |
| Event handlers | sync only | sync or async |
| `verify_webhook_signature` | sync | sync (no I/O) |
| `process_webhook` | sync dispatch | async dispatch |

## FastAPI Example

```python
from fastapi import FastAPI, Request
from solanaeasy import AsyncSolanaEasy

app = FastAPI()
sdk = AsyncSolanaEasy(api_key="sk_test_...", webhook_secret="whsec_...")

@sdk.on("payment.confirmed")
async def on_confirmed(event):
    print(f"Payment confirmed: {event.session_id}")

@app.post("/checkout")
async def create_checkout():
    session = await sdk.create_payment(
        amount=150.00,
        order_id="web_001",
        description="Premium Subscription",
    )
    return {"payment_url": session.payment_url}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-SolanaEasy-Signature", "")
    await sdk.process_webhook(payload=body, signature=sig)
    return {"ok": True}
```
