# SolanaEasy Python SDK

> **The Stripe for Solana** — integrate blockchain payments in less than 10 lines. No blockchain knowledge required.

[![PyPI version](https://badge.fury.io/py/solanaeasy.svg)](https://badge.fury.io/py/solanaeasy)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quickstart

```bash
pip install solanaeasy
```

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(api_key="sk_test_...")

# Create a payment session
session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="order_123",
    description="Nike Air Max",
)

print(session.payment_url)   # → redirect your customer here
print(session.session_id)    # → save this to track the payment

# Wait for confirmation (auto-polling, no loop needed)
status = sdk.wait_for_confirmation(session.session_id, timeout=120)
print(status.human_message)  # → "Payment confirmed in 2.3s"
```

---

## Why SolanaEasy?

| Without SolanaEasy | With SolanaEasy |
|---|---|
| Manage cryptographic keypairs | `sdk.create_payment(amount=50.00, ...)` |
| Sign transactions manually | `sdk.check_status(session_id)` |
| Parse RPC errors | `status.human_message` in plain English |
| Build webhook verification | `sdk.verify_webhook_signature(payload, sig)` |
| Write polling loops | `sdk.wait_for_confirmation(session_id)` |

---

## Installation

```bash
# Core SDK (calls SolanaEasy backend)
pip install solanaeasy

# With direct Solana network access
pip install solanaeasy[solana]
```

---

## Methods

| Method | Description |
|---|---|
| `create_payment(amount, currency, order_id, description)` | Creates a payment session, returns `payment_url` and `session_id` |
| `check_status(session_id)` | Returns current state + human-readable message |
| `wait_for_confirmation(session_id, timeout, on_update)` | Blocks until confirmed/failed/expired — no polling loop needed |
| `list_payments(status, limit, offset)` | Lists merchant payments with optional filters |
| `register_webhook(url)` | Registers a URL to receive real-time payment events |
| `verify_webhook_signature(payload, signature)` | Verifies HMAC-SHA256 webhook signature (anti-replay) |
| `process_webhook(payload, signature)` | Verifies + parses + dispatches to `@sdk.on()` handlers |
| `refund(session_id)` | Initiates a refund *(coming in Phase 4)* |

---

## Payment States

```
CREATED → PENDING → CONFIRMED ✅
                 └→ FAILED    ❌
                 └→ EXPIRED   ⌛ (15 min timeout)
```

---

## Error Handling

```python
from solanaeasy import SolanaEasy
from solanaeasy.exceptions import (
    InsufficientFunds,
    SessionNotFoundError,
    WaitTimeout,
    RateLimitError,
)

sdk = SolanaEasy(api_key="sk_test_...")

try:
    status = sdk.wait_for_confirmation(session.session_id, timeout=60)

except WaitTimeout as e:
    print(f"Still {e.last_status.state} after {e.timeout}s")

except InsufficientFunds:
    print("Customer wallet has insufficient balance")

except SessionNotFoundError:
    print("Session not found")

except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
```

---

## Webhooks

```python
sdk = SolanaEasy(api_key="sk_...", webhook_secret="whsec_...")

# Register handlers using the decorator
@sdk.on("payment.confirmed")
def on_confirmed(event):
    fulfill_order(event.session_id)
    print(event.data.human_message)  # "Payment confirmed in 2.3s"

@sdk.on("payment.failed")
def on_failed(event):
    notify_customer(event.session_id)

# In your webhook endpoint (Flask / FastAPI / Django)
@app.post("/webhook/solana")
def webhook_endpoint(request):
    sdk.process_webhook(
        payload=request.body,
        signature=request.headers["X-SolanaEasy-Signature"],
    )
    return 200
```

---

## Async Support

```python
from solanaeasy import AsyncSolanaEasy

async def process_order():
    async with AsyncSolanaEasy(api_key="sk_...") as sdk:
        session = await sdk.create_payment(
            amount=50.00,
            order_id="order_123",
            idempotency_key="order_123_v1",  # prevents duplicate charges on retry
        )
        status = await sdk.wait_for_confirmation(session.session_id, timeout=120)
        return status
```

---

## CLI

```bash
# Check payment status
solanaeasy status sess_abc123

# List recent payments
solanaeasy payments --status CONFIRMED --limit 10

# Watch a payment in real-time
solanaeasy wait sess_abc123 --timeout 120
```

---

## Environment Variables

```bash
SOLANAEASY_API_KEY=sk_test_...          # required
SOLANAEASY_NETWORK=devnet               # devnet | mainnet-beta
SOLANAEASY_BASE_URL=http://localhost:8000
SOLANAEASY_WEBHOOK_SECRET=whsec_...
```

---

## Idempotency

Pass `idempotency_key` to prevent duplicate charges on network retries:

```python
session = sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    idempotency_key="order_123_attempt_1",
)
# Calling twice with the same key returns the original session
```

---

## License

MIT © SolanaEasy — UNICAMP Hackathon Team
