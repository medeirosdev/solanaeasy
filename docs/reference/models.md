# Models

All models are immutable Pydantic BaseModels (`frozen=True`).

## PaymentSession

Returned by `create_payment()` and `list_payments()`.

```python
class PaymentSession(BaseModel):
    session_id: str
    payment_url: str
    amount: float
    currency: str            # default: "USDC"
    order_id: str
    description: str
    state: PaymentState
    wallet_public_key: str | None
    metadata: dict[str, str] | None
    created_at: datetime
    expires_at: datetime
```

### Properties

| Property | Type | Description |
|---|---|---|
| `is_confirmed` | `bool` | `True` if `state == "CONFIRMED"` |
| `is_expired` | `bool` | `True` if `now > expires_at` |

### Example

```python
session = sdk.create_payment(amount=50.00, order_id="o1")

print(session.session_id)         # "sess_abc123"
print(session.wallet_public_key)  # "A97aWAnLj2g..."
print(session.is_confirmed)       # False
print(session.is_expired)         # False
```

---

## PaymentStatus

Returned by `check_status()`, `wait_for_confirmation()`, `cancel_session()`, and `refund()`.

```python
class PaymentStatus(BaseModel):
    session_id: str
    state: PaymentState
    human_message: str
    wallet_public_key: str | None
    tx_hash: str | None              # Set when CONFIRMED
    confirmed_at: datetime | None    # Set when CONFIRMED
    confirmation_time_ms: int | None # Set when CONFIRMED
    error_code: str | None           # Set when FAILED
```

### Example

```python
status = sdk.check_status("sess_abc123")

if status.state == "CONFIRMED":
    print(f"Tx: {status.tx_hash}")
    print(f"Confirmed in {status.confirmation_time_ms}ms")
elif status.state == "FAILED":
    print(f"Error: {status.error_code}")
```

---

## WebhookEvent

Received by webhook handlers registered with `@sdk.on()`.

```python
class WebhookEvent(BaseModel):
    event_type: WebhookEventType
    session_id: str
    timestamp: datetime
    data: PaymentStatus
```

### Example Payload

```json
{
    "event_type": "payment.confirmed",
    "session_id": "sess_abc123",
    "timestamp": "2026-05-05T19:30:00Z",
    "data": {
        "session_id": "sess_abc123",
        "state": "CONFIRMED",
        "human_message": "Payment confirmed on the Solana Devnet.",
        "wallet_public_key": "A97aWAnLj2g...",
        "tx_hash": "5KtP9...",
        "confirmed_at": "2026-05-05T19:30:00Z",
        "confirmation_time_ms": 2300,
        "error_code": null
    }
}
```

---

## PaymentReceipt

Returned by `get_receipt()`. Available for `CONFIRMED` and `REFUNDED` sessions.

```python
class PaymentReceipt(BaseModel):
    session_id: str
    order_id: str
    description: str
    amount: float
    currency: str
    amount_brl: float | None
    tx_hash: str
    block_number: int | None
    confirmed_at: datetime
    confirmation_time_ms: int | None
    explorer_url: str
```

### Example

```python
receipt = sdk.get_receipt("sess_abc123")
print(receipt.explorer_url)
# "https://explorer.solana.com/tx/5KtP9...?cluster=devnet"
```

---

## Type Aliases

### PaymentState

```python
PaymentState = Literal[
    "CREATED",
    "PENDING",
    "CONFIRMED",
    "FAILED",
    "EXPIRED",
    "CANCELLED",
    "REFUNDED",
]
```

### WebhookEventType

```python
WebhookEventType = Literal[
    "payment.confirmed",
    "payment.failed",
    "payment.expired",
    "payment.pending",
]
```
