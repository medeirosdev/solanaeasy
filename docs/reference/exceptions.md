# Exceptions

All exceptions inherit from `SolanaEasyError` and include a `message` and optional `code` attribute.

## Hierarchy

```
SolanaEasyError(Exception)
├── AuthenticationError
├── PaymentError
│   ├── InsufficientFunds
│   ├── TransactionExpired
│   └── NetworkCongestion
├── SessionNotFoundError
├── WebhookError
├── RateLimitError
└── WaitTimeout
```

---

## SolanaEasyError

Base class for all SDK errors.

```python
class SolanaEasyError(Exception):
    message: str
    code: str | None
```

---

## AuthenticationError

API key is invalid, expired, or missing.

- **Triggered by:** HTTP 401
- **Code:** `INVALID_API_KEY`

```python
try:
    sdk = SolanaEasy(api_key="bad_key")
    sdk.create_payment(amount=50, order_id="o1")
except AuthenticationError as e:
    print(e.message)  # "API key inválida ou expirada..."
```

---

## PaymentError

Base class for payment-specific errors.

### InsufficientFunds

Customer wallet doesn't have enough balance.

- **On-chain:** `insufficient funds for instruction`
- **Code:** `INSUFFICIENT_FUNDS`

### TransactionExpired

Transaction blockhash expired before being confirmed.

- **On-chain:** `blockhash not found`
- **Code:** `TRANSACTION_EXPIRED`

### NetworkCongestion

Solana network is congested. Also raised on HTTP timeouts after 3 retries.

- **On-chain:** `transaction timeout`
- **Code:** `REQUEST_TIMEOUT`

---

## SessionNotFoundError

The `session_id` doesn't exist in the backend.

- **Triggered by:** HTTP 404
- **Code:** `NOT_FOUND`

---

## WebhookError

Webhook signature verification failed.

- **Codes:** `INVALID_WEBHOOK_SIGNATURE`, `INVALID_WEBHOOK_PAYLOAD`, `MISSING_WEBHOOK_SECRET`

---

## RateLimitError

Too many requests. The backend returned HTTP 429.

```python
class RateLimitError(SolanaEasyError):
    retry_after: int | None  # Seconds to wait
```

---

## WaitTimeout

`wait_for_confirmation()` reached its timeout.

```python
class WaitTimeout(SolanaEasyError):
    last_status: PaymentStatus  # Last known status
    timeout: int                # Seconds waited
```

```python
try:
    sdk.wait_for_confirmation("sess_abc", timeout=30)
except WaitTimeout as e:
    print(f"Still {e.last_status.state} after {e.timeout}s")
```

---

## Import

```python
from solanaeasy.exceptions import (
    SolanaEasyError,
    AuthenticationError,
    PaymentError,
    InsufficientFunds,
    TransactionExpired,
    NetworkCongestion,
    SessionNotFoundError,
    WebhookError,
    RateLimitError,
    WaitTimeout,
)
```
