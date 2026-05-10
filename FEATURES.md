# SolanaEasy Python SDK -- Features

> Living document. Updated with each new feature.
> Last update: 2026-05-05

---

## Feature Status

| Feature | Status | Module |
|---|---|---|
| `create_payment()` | Implemented | `client.py` |
| `check_status()` | Implemented | `client.py` |
| `list_payments()` | Implemented | `client.py` |
| `wait_for_confirmation()` | Implemented | `client.py` |
| `register_webhook()` | Implemented | `client.py` |
| `verify_webhook_signature()` | Implemented | `client.py` + `_internal/webhook.py` |
| `process_webhook()` + `@sdk.on()` | Implemented | `client.py` |
| `refund()` | Implemented | `client.py` |
| `cancel_session()` | Implemented | `client.py` |
| `get_receipt()` | Implemented | `client.py` |
| `get_wallet_balance()` | Implemented | `client.py` |
| Custom metadata | Implemented | `client.py` + `models.py` |
| Idempotency key | Implemented | `client.py` |
| `AsyncSolanaEasy` | Implemented | `async_client.py` |
| CLI (`solanaeasy status`, `payments`, `wait`) | Implemented | `cli.py` |
| `py.typed` (mypy support) | Implemented | `py.typed` |
| Wallet public key in responses | Implemented | `models.py` |
| CANCELLED / REFUNDED states | Implemented | `models.py` |

---

## Feature Details

---

### `create_payment()` -- Create a payment session

```python
session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="pedido_123",
    description="Nike Air Max",
    idempotency_key="pedido_123_v1",
    metadata={"user_id": "u_42", "sku": "NIKE-AM-001"},
)
print(session.payment_url)        # URL for the customer to pay
print(session.session_id)         # ID to track later
print(session.wallet_public_key)  # Solana deposit address
print(session.metadata)           # Your custom metadata
```

**Parameters:**
- `amount` (float, required) -- value to charge, must be > 0
- `currency` (str, default `"USDC"`) -- stablecoin currency
- `order_id` (str, required) -- order ID in the merchant's system
- `description` (str, optional) -- appears on the receipt
- `expires_in` (int, default `900`) -- seconds until expiry
- `idempotency_key` (str, optional) -- unique key to prevent duplicate charges
- `metadata` (dict, optional) -- custom key-value pairs stored server-side

**Returns:** `PaymentSession`

---

### `check_status()` -- Check payment status

```python
status = sdk.check_status(session.session_id)
print(status.state)               # "PENDING" | "CONFIRMED" | "FAILED" | "EXPIRED"
print(status.human_message)       # "Payment confirmed on the Solana Devnet."
print(status.wallet_public_key)   # Deposit address
print(status.tx_hash)             # Transaction hash (if confirmed)
```

**Returns:** `PaymentStatus`

---

### `wait_for_confirmation()` -- Wait for payment

Blocks until the payment reaches a terminal state. No manual polling loop needed.

```python
try:
    status = sdk.wait_for_confirmation(
        session.session_id,
        timeout=120,
        poll_interval=2.0,
        on_update=lambda s: print(f"State: {s.state}"),
    )
    print(status.human_message)
except WaitTimeout as e:
    print(f"Timeout! Last state: {e.last_status.state}")
```

**Terminal states:** `CONFIRMED`, `FAILED`, `EXPIRED`
**Raises:** `WaitTimeout` if timeout is reached

---

### `cancel_session()` -- Cancel before payment

```python
status = sdk.cancel_session(session.session_id)
print(status.state)  # "CANCELLED"
```

Only sessions in CREATED or PENDING state can be cancelled.
Raises HTTP 409 if the session has already been confirmed, failed, or expired.

---

### `refund()` -- Refund a confirmed payment

```python
status = sdk.refund(session.session_id)
print(status.state)          # "REFUNDED"
print(status.human_message)  # "Payment refunded by merchant."
```

Only CONFIRMED sessions can be refunded.
Raises HTTP 409 for any other state.

---

### `get_receipt()` -- Get payment receipt

```python
receipt = sdk.get_receipt(session.session_id)
print(receipt.explorer_url)       # Link to Solana Explorer
print(receipt.tx_hash)            # Transaction hash
print(receipt.amount)             # Amount paid
print(receipt.confirmation_time_ms)  # Confirmation time in ms
```

Available for CONFIRMED and REFUNDED sessions.

---

### `get_wallet_balance()` -- Check wallet balance

```python
info = sdk.get_wallet_balance(session.session_id)
print(f"Wallet:  {info['wallet_public_key']}")
print(f"Balance: {info['sol_balance']} SOL")
print(f"Network: {info['network']}")
```

Queries the real SOL balance on-chain via Solana RPC.

---

### Custom Metadata

Attach arbitrary key-value pairs to any payment session. Metadata is stored
server-side and returned in `check_status()`, `list_payments()`, and webhook events.

```python
session = sdk.create_payment(
    amount=50.00,
    order_id="pedido_123",
    metadata={
        "user_id": "u_42",
        "sku": "NIKE-AM-001",
        "discount_code": "HACKATHON10",
    },
)
print(session.metadata)  # {"user_id": "u_42", "sku": "NIKE-AM-001", ...}
```

---

### Idempotency Key

Prevents duplicate charges on retry. Same key returns the original session.

```python
for _ in range(2):
    session = sdk.create_payment(
        amount=50.00,
        order_id="pedido_123",
        idempotency_key="pedido_123_attempt_1",
    )
# session.session_id is identical in both calls
```

Sent as HTTP header: `Idempotency-Key: pedido_123_attempt_1`

---

### Webhook Signature Verification

Ensures payload authenticity via HMAC-SHA256 with timestamp protection.

```python
sdk = SolanaEasy(api_key="sk_...", webhook_secret="whsec_...")

@app.post("/webhook/solana")
def handle_webhook(request):
    try:
        event = sdk.verify_webhook_signature(
            payload=request.body,
            signature=request.headers["X-SolanaEasy-Signature"],
        )
        print(event.event_type)  # "payment.confirmed"
    except WebhookError:
        return 400
```

**Algorithm:** HMAC-SHA256 with timestamp (rejects replays older than 5 min)
**Header:** `X-SolanaEasy-Signature: t=1234567890,v1=abc123...`

---

### `@sdk.on()` -- Webhook Event Decorator

```python
@sdk.on("payment.confirmed")
def on_confirmed(event: WebhookEvent):
    fulfill_order(event.session_id)

@sdk.on("payment.failed")
def on_failed(event: WebhookEvent):
    notify_customer(event.session_id, event.data.human_message)

@app.post("/webhook/solana")
def webhook_endpoint(request):
    sdk.process_webhook(
        payload=request.body,
        signature=request.headers["X-SolanaEasy-Signature"],
    )
    return 200
```

---

### `AsyncSolanaEasy` -- Async Client

Same interface as `SolanaEasy`, but with `async/await`. Ideal for FastAPI.

```python
from solanaeasy import AsyncSolanaEasy

async def process_order():
    async with AsyncSolanaEasy(api_key="sk_...") as sdk:
        session = await sdk.create_payment(amount=50.00, order_id="pedido_123")
        status = await sdk.wait_for_confirmation(session.session_id, timeout=120)
        return status
```

---

### CLI -- Command Line Interface

```bash
# Check payment status
$ solanaeasy status sess_abc123

# List recent payments
$ solanaeasy payments --limit 5
$ solanaeasy payments --status CONFIRMED

# Wait for confirmation in real-time
$ solanaeasy wait sess_abc123

# Help
$ solanaeasy --help
```

---

## Data Models

### `PaymentSession`
| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Unique session ID |
| `payment_url` | `str` | URL for customer to pay |
| `amount` | `float` | Amount charged (> 0) |
| `currency` | `str` | Currency (default: USDC) |
| `order_id` | `str` | Merchant's order ID |
| `description` | `str` | Product description |
| `state` | `PaymentState` | Current state |
| `wallet_public_key` | `str or None` | Solana deposit address |
| `metadata` | `dict or None` | Custom merchant metadata |
| `created_at` | `datetime` | Creation timestamp |
| `expires_at` | `datetime` | Expiration timestamp |
| `is_confirmed` | `bool` (property) | Shortcut: state == CONFIRMED |
| `is_expired` | `bool` (property) | Shortcut: now > expires_at |

### `PaymentStatus`
| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Session ID |
| `state` | `PaymentState` | Current state |
| `human_message` | `str` | Human-readable message |
| `wallet_public_key` | `str or None` | Solana deposit address |
| `tx_hash` | `str or None` | Solana tx hash (if confirmed) |
| `confirmed_at` | `datetime or None` | Confirmation timestamp |
| `confirmation_time_ms` | `int or None` | Confirmation time in ms |
| `error_code` | `str or None` | On-chain error code (if failed) |

---

## Payment States

```
CREATED     Session created, waiting for customer
PENDING     Customer initiated payment, awaiting network confirmation
CONFIRMED   Transaction finalized on-chain
FAILED      Transaction rejected
EXPIRED     Session timed out without payment
CANCELLED   Session cancelled by merchant before payment
REFUNDED    Confirmed payment refunded by merchant
```

---

## Exceptions

| Exception | When |
|---|---|
| `SolanaEasyError` | Base for all errors |
| `AuthenticationError` | Invalid or missing API key |
| `PaymentError` | Generic payment flow error |
| `InsufficientFunds` | Customer wallet has insufficient balance |
| `TransactionExpired` | Blockhash expired before confirmation |
| `NetworkCongestion` | Solana network congested |
| `SessionNotFoundError` | session_id not found |
| `WebhookError` | Invalid signature or webhook failure |
| `RateLimitError` | Too many requests (has `.retry_after`) |
| `WaitTimeout` | `wait_for_confirmation()` timed out (has `.last_status`) |
