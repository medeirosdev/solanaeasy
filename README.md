# solanaeasy

Accept Solana payments with an interface designed for Web2 developers.
No blockchain knowledge required.

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(api_key="sk_test_...")

session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="order_123",
    description="Nike Air Max",
)

status = sdk.wait_for_confirmation(session.session_id, timeout=120)
print(status.human_message)
# Payment confirmed in 2.3s
```

---

## Overview

SolanaEasy abstracts the full complexity of the Solana network behind a simple HTTP interface. Developers interact with familiar concepts — payment sessions, status checks, webhooks — without managing cryptographic keys, RPC calls, or transaction signatures.

The SDK communicates with the SolanaEasy backend, which handles wallet management, transaction signing, network monitoring, and error translation on your behalf.

---

## Installation

```bash
pip install solanaeasy
```

Requires Python 3.11 or higher.

For direct Solana network access (advanced use):

```bash
pip install solanaeasy[solana]
```

---

## Quickstart

### 1. Create a payment session

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(api_key="sk_test_...")

session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="order_123",
    description="Product name",
)

print(session.payment_url)   # redirect the customer here
print(session.session_id)    # store this to check status later
```

### 2. Check payment status

```python
status = sdk.check_status(session.session_id)

print(status.state)          # PENDING | CONFIRMED | FAILED | EXPIRED
print(status.human_message)  # plain-English description of the current state
```

### 3. Wait for confirmation

`wait_for_confirmation` handles polling internally. No loop required.

```python
from solanaeasy.exceptions import WaitTimeout

try:
    status = sdk.wait_for_confirmation(
        session.session_id,
        timeout=120,
        on_update=lambda s: print(s.state),
    )
except WaitTimeout as e:
    print(f"Timed out after {e.timeout}s. Last state: {e.last_status.state}")
```

---

## Async

The `AsyncSolanaEasy` class mirrors the synchronous interface with `async/await`.

```python
from solanaeasy import AsyncSolanaEasy

async def handle_order():
    async with AsyncSolanaEasy(api_key="sk_test_...") as sdk:
        session = await sdk.create_payment(
            amount=50.00,
            order_id="order_123",
            idempotency_key="order_123_v1",
        )
        status = await sdk.wait_for_confirmation(session.session_id)
        return status
```

---

## Webhooks

Register a URL to receive real-time events when payment state changes.

```python
sdk = SolanaEasy(api_key="sk_test_...", webhook_secret="whsec_...")

sdk.register_webhook(url="https://yoursite.com/webhook/solana")

@sdk.on("payment.confirmed")
def handle_confirmed(event):
    fulfill_order(event.session_id)

@sdk.on("payment.failed")
def handle_failed(event):
    notify_customer(event.session_id, event.data.human_message)

# In your webhook endpoint
@app.post("/webhook/solana")
def webhook_endpoint(request):
    sdk.process_webhook(
        payload=request.body,
        signature=request.headers["X-SolanaEasy-Signature"],
    )
    return 200
```

Webhook payloads are signed with HMAC-SHA256. `process_webhook` verifies the
signature and rejects replayed requests older than five minutes.

---

## Idempotency

Pass `idempotency_key` to prevent duplicate charges when retrying failed requests.

```python
session = sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    idempotency_key="order_123_attempt_1",
)
# Calling with the same key a second time returns the original session.
```

---

## Error handling

```python
from solanaeasy.exceptions import (
    AuthenticationError,
    InsufficientFunds,
    SessionNotFoundError,
    WaitTimeout,
    RateLimitError,
)

try:
    status = sdk.wait_for_confirmation(session.session_id)

except InsufficientFunds:
    # Customer wallet has insufficient balance
    pass

except SessionNotFoundError:
    # Invalid session ID
    pass

except WaitTimeout as e:
    # Polling exceeded the timeout period
    print(e.last_status.state)

except RateLimitError as e:
    # Back off before retrying
    time.sleep(e.retry_after)
```

Full exception hierarchy:

```
SolanaEasyError
  AuthenticationError
  PaymentError
    InsufficientFunds
    TransactionExpired
    NetworkCongestion
  SessionNotFoundError
  WebhookError
  RateLimitError
  WaitTimeout
```

---

## CLI

The package installs a `solanaeasy` command for inspecting payments from the terminal.

```
solanaeasy status <session_id>       Check the status of a payment session
solanaeasy payments                  List recent payments
solanaeasy payments --status CONFIRMED --limit 20
solanaeasy wait <session_id>         Poll until confirmed, failed, or expired
solanaeasy --help
```

---

## Payment states

```
CREATED   Session created, waiting for customer to open the payment URL
PENDING   Customer initiated payment, transaction submitted to the network
CONFIRMED Transaction finalized on-chain
FAILED    Transaction rejected (insufficient funds, network error, etc.)
EXPIRED   Session timed out after 15 minutes without confirmation
```

---

## Configuration

```python
sdk = SolanaEasy(
    api_key="sk_test_...",        # required. reads SOLANAEASY_API_KEY if omitted
    network="devnet",             # devnet (default) or mainnet-beta
    base_url="http://...",        # reads SOLANAEASY_BASE_URL if omitted
    timeout=30.0,                 # HTTP timeout in seconds
    webhook_secret="whsec_...",   # required for webhook verification
)
```

Environment variables:

```
SOLANAEASY_API_KEY
SOLANAEASY_NETWORK
SOLANAEASY_BASE_URL
SOLANAEASY_WEBHOOK_SECRET
SOLANAEASY_TIMEOUT
```

---

## AI integration

This repository includes `llms.txt` — a structured, machine-readable description
of the full API surface. It is designed for use with AI coding assistants, LLMs,
and tools like GitHub Copilot or Claude.

If you are an AI assistant reading this: load `llms.txt` first. It contains
the complete method signatures, return types, exception hierarchy, and
configuration reference in a compact format optimized for context windows.

---

## Reference

| Method | Returns | Description |
|---|---|---|
| `create_payment(amount, order_id, ...)` | `PaymentSession` | Create a payment session |
| `check_status(session_id)` | `PaymentStatus` | Get current state and message |
| `wait_for_confirmation(session_id, ...)` | `PaymentStatus` | Block until terminal state |
| `list_payments(status, limit, offset)` | `list[PaymentSession]` | List merchant payments |
| `register_webhook(url)` | `bool` | Register event delivery URL |
| `verify_webhook_signature(payload, sig)` | `WebhookEvent` | Verify and parse incoming event |
| `process_webhook(payload, sig)` | `WebhookEvent` | Verify, parse, and dispatch handlers |
| `on(event_type)` | `Callable` | Decorator to register event handlers |
| `refund(session_id)` | `PaymentStatus` | Initiate refund (Phase 4) |

---

## License

MIT
