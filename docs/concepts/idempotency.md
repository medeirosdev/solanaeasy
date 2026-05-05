# Idempotency

Idempotency prevents duplicate charges when retrying failed requests.

## How It Works

Pass an `idempotency_key` when creating a payment. If the same key is used again, the original session is returned instead of creating a new charge.

```python
# First call — creates the session
session = sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    idempotency_key="order_123_attempt_1",
)

# Second call with same key — returns the SAME session
session2 = sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    idempotency_key="order_123_attempt_1",
)

assert session.session_id == session2.session_id  # True
```

## Implementation

The idempotency key is sent as an HTTP header:

```
Idempotency-Key: order_123_attempt_1
```

The backend stores the key alongside the session. Subsequent requests with the same key and merchant ID return the existing session without side effects.

## Best Practices

!!! tip "Key format"
    Use a combination of your order ID and attempt number:
    ```python
    idempotency_key=f"{order_id}_attempt_{attempt}"
    ```

!!! warning "Keys are scoped to merchants"
    Two different merchants can use the same idempotency key without conflict.

!!! info "Key expiration"
    Idempotency keys are valid for the lifetime of the session (default: 15 minutes).
