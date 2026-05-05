# SolanaEasy (Synchronous Client)

The main SDK client. All methods are synchronous (blocking).

## Constructor

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(
    api_key="sk_test_...",        # Required (or set SOLANAEASY_API_KEY)
    network="devnet",             # "devnet" | "mainnet-beta"
    base_url="http://...",        # Override backend URL
    timeout=30.0,                 # HTTP timeout in seconds
    webhook_secret="whsec_...",   # Required for webhook verification
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str \| None` | env var | API key from the dashboard |
| `network` | `str` | `"devnet"` | Solana network |
| `base_url` | `str \| None` | auto | Backend URL (auto-detected from network) |
| `timeout` | `float` | `30.0` | HTTP request timeout |
| `webhook_secret` | `str \| None` | env var | Secret for webhook signature verification |

## Payment Methods

---

### `create_payment()`

Creates a new payment session with a unique Solana wallet.

```python
session = sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    currency="USDC",
    description="Nike Air Max",
    expires_in=900,
    idempotency_key="order_123_v1",
    metadata={"user_id": "u_42", "sku": "NIKE-001"},
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `amount` | `float` | Yes | — | Amount to charge (must be > 0) |
| `order_id` | `str` | Yes | — | Your internal order ID |
| `currency` | `str` | No | `"USDC"` | Currency code |
| `description` | `str` | No | `""` | Product description |
| `expires_in` | `int` | No | `900` | Seconds until session expires |
| `idempotency_key` | `str` | No | `None` | Prevents duplicate charges |
| `metadata` | `dict[str, str]` | No | `None` | Custom key-value pairs |

**Returns:** [`PaymentSession`](models.md#paymentsession)

**Raises:** `SolanaEasyError` if amount ≤ 0 or order_id is empty.

---

### `check_status()`

Gets the current status of a payment session.

```python
status = sdk.check_status("sess_abc123")
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `str` | Session ID from `create_payment()` |

**Returns:** [`PaymentStatus`](models.md#paymentstatus)

---

### `wait_for_confirmation()`

Blocks until the payment reaches a terminal state (`CONFIRMED`, `FAILED`, or `EXPIRED`).

```python
status = sdk.wait_for_confirmation(
    "sess_abc123",
    timeout=120,
    poll_interval=2.0,
    on_update=lambda s: print(s.state),
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `session_id` | `str` | — | Session to monitor |
| `timeout` | `int` | `120` | Max seconds to wait |
| `poll_interval` | `float` | `2.0` | Seconds between status checks |
| `on_update` | `Callable` | `None` | Called on each state change |

**Returns:** [`PaymentStatus`](models.md#paymentstatus)

**Raises:** [`WaitTimeout`](exceptions.md#waittimeout) if timeout is reached.

---

### `list_payments()`

Lists payment sessions for the current merchant.

```python
payments = sdk.list_payments(status="CONFIRMED", limit=20, offset=0)
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | `str \| None` | `None` | Filter by state |
| `limit` | `int` | `20` | Max results |
| `offset` | `int` | `0` | Pagination offset |

**Returns:** `list[PaymentSession]`

---

### `cancel_session()`

Cancels a session that has not been paid yet.

```python
status = sdk.cancel_session("sess_abc123")
```

Only sessions in `CREATED` or `PENDING` state can be cancelled.

**Returns:** [`PaymentStatus`](models.md#paymentstatus) with `state == "CANCELLED"`

**Raises:** HTTP 409 if the session cannot be cancelled.

---

### `refund()`

Refunds a confirmed payment.

```python
status = sdk.refund("sess_abc123")
```

Only sessions in `CONFIRMED` state can be refunded.

**Returns:** [`PaymentStatus`](models.md#paymentstatus) with `state == "REFUNDED"`

**Raises:** HTTP 409 if the session cannot be refunded.

---

### `get_receipt()`

Gets a formatted receipt for a confirmed payment.

```python
receipt = sdk.get_receipt("sess_abc123")
print(receipt.explorer_url)
```

Available for `CONFIRMED` and `REFUNDED` sessions.

**Returns:** [`PaymentReceipt`](models.md#paymentreceipt)

---

### `get_wallet_balance()`

Checks the real-time SOL balance of a session's wallet.

```python
info = sdk.get_wallet_balance("sess_abc123")
# {"wallet_public_key": "...", "sol_balance": 1.5, "network": "devnet"}
```

**Returns:** `dict` with keys `wallet_public_key`, `sol_balance`, `network`.

---

## Webhook Methods

### `register_webhook()`

Registers a URL to receive payment events.

```python
sdk.register_webhook(url="https://yoursite.com/webhook/solana")
```

**Returns:** `bool` (True on success)

---

### `verify_webhook_signature()`

Verifies a webhook payload signature without dispatching handlers.

```python
event = sdk.verify_webhook_signature(
    payload=raw_body,       # bytes
    signature=sig_header,   # X-SolanaEasy-Signature header value
)
```

**Returns:** [`WebhookEvent`](models.md#webhookevent)

**Raises:** [`WebhookError`](exceptions.md#webhookerror)

---

### `process_webhook()`

Verifies signature and dispatches to all registered `@sdk.on()` handlers.

```python
event = sdk.process_webhook(
    payload=raw_body,
    signature=sig_header,
)
```

**Returns:** [`WebhookEvent`](models.md#webhookevent)

---

### `on()` decorator

Registers an event handler for a specific webhook event type.

```python
@sdk.on("payment.confirmed")
def handle_confirmed(event: WebhookEvent):
    fulfill_order(event.session_id)
```

**Valid event types:** `payment.confirmed`, `payment.failed`, `payment.expired`, `payment.pending`

---

## Context Manager

```python
with SolanaEasy(api_key="sk_test_...") as sdk:
    session = sdk.create_payment(amount=50.00, order_id="o1")
    # Connection is closed automatically
```

Or manually:

```python
sdk = SolanaEasy(api_key="sk_test_...")
# ... use the SDK ...
sdk.close()
```
