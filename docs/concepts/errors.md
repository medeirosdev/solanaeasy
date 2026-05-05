# Error Handling

SolanaEasy provides a structured exception hierarchy that maps HTTP errors and Solana network errors to developer-friendly Python exceptions.

## Exception Hierarchy

```
SolanaEasyError
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

## Catching Errors

```python
from solanaeasy.exceptions import (
    AuthenticationError,
    InsufficientFunds,
    SessionNotFoundError,
    WaitTimeout,
    RateLimitError,
    SolanaEasyError,
)

try:
    status = sdk.wait_for_confirmation(session.session_id)

except AuthenticationError:
    # Invalid or expired API key
    print("Check your API key")

except InsufficientFunds:
    # Customer wallet doesn't have enough balance
    print("Please add funds to your wallet")

except SessionNotFoundError:
    # The session_id doesn't exist
    print("Invalid session")

except WaitTimeout as e:
    # Polling timed out before reaching a terminal state
    print(f"Last state: {e.last_status.state}")
    print(f"Waited: {e.timeout} seconds")

except RateLimitError as e:
    # Too many requests — back off
    print(f"Retry after {e.retry_after} seconds")
    time.sleep(e.retry_after)

except SolanaEasyError as e:
    # Catch-all for any SDK error
    print(f"Error: {e.message}")
    print(f"Code: {e.code}")
```

## Exception Details

### `SolanaEasyError`

Base class for all SDK errors.

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable error message |
| `code` | `str \| None` | Machine-readable error code for logging |

### `AuthenticationError`

Raised when the API key is invalid, expired, or missing.

- **HTTP Status**: 401
- **Code**: `INVALID_API_KEY`

### `PaymentError`

Base class for payment-specific errors.

#### `InsufficientFunds`

Customer wallet doesn't have enough balance.

- **On-chain error**: `insufficient funds for instruction`

#### `TransactionExpired`

Transaction blockhash expired before confirmation.

- **On-chain error**: `blockhash not found`

#### `NetworkCongestion`

Solana network is congested. Transaction wasn't processed in time.

- **On-chain error**: `transaction timeout`
- **Also raised on**: HTTP timeout after 3 retries

### `SessionNotFoundError`

The `session_id` doesn't exist in the backend.

- **HTTP Status**: 404
- **Code**: `NOT_FOUND`

### `WaitTimeout`

`wait_for_confirmation()` reached its timeout without the payment reaching a terminal state.

| Attribute | Type | Description |
|---|---|---|
| `last_status` | `PaymentStatus` | Last known status before timeout |
| `timeout` | `int` | Number of seconds waited |

### `WebhookError`

Webhook signature verification failed.

- **Codes**: `INVALID_WEBHOOK_SIGNATURE`, `INVALID_WEBHOOK_PAYLOAD`

### `RateLimitError`

Too many requests. The backend returned HTTP 429.

| Attribute | Type | Description |
|---|---|---|
| `retry_after` | `int \| None` | Seconds to wait before retrying |

## HTTP Error Mapping

| HTTP Status | SDK Exception |
|---|---|
| 401 | `AuthenticationError` |
| 404 | `SessionNotFoundError` |
| 429 | `RateLimitError` |
| 502, 503, 504 | Auto-retry (up to 3 times), then `SolanaEasyError` |
| Other 4xx/5xx | `SolanaEasyError` |

## Automatic Retries

The SDK automatically retries requests on:

- HTTP 502, 503, 504 (server errors)
- Connection timeouts

Retry delays use exponential backoff: **1s → 2s → 4s** (max 3 attempts).
