# Quickstart

This guide walks you through creating your first payment in under 2 minutes.

## 1. Initialize the SDK

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(api_key="sk_test_1234567890")
```

!!! tip "Using environment variables"
    If `SOLANAEASY_API_KEY` is set in your environment, you can omit the `api_key` parameter:
    ```python
    sdk = SolanaEasy()  # reads from environment
    ```

## 2. Create a Payment Session

```python
session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="order_123",
    description="Nike Air Max Pulse",
    metadata={"user_id": "u_42"},  # optional custom data
)

print(session.session_id)         # "sess_abc123..."
print(session.payment_url)        # URL to redirect customer
print(session.wallet_public_key)  # Solana deposit address
```

The SDK creates a unique Solana wallet for this payment. The customer deposits funds to this address.

## 3. Check Payment Status

```python
status = sdk.check_status(session.session_id)

print(status.state)          # "CREATED" | "PENDING" | "CONFIRMED" | ...
print(status.human_message)  # Human-readable description
```

## 4. Wait for Confirmation

Instead of writing your own polling loop, use `wait_for_confirmation`:

```python
from solanaeasy.exceptions import WaitTimeout

try:
    status = sdk.wait_for_confirmation(
        session.session_id,
        timeout=120,  # seconds
        on_update=lambda s: print(f"State: {s.state}"),
    )
    print(f"Payment {status.state}!")
    print(f"Tx hash: {status.tx_hash}")
except WaitTimeout as e:
    print(f"Timed out. Last state: {e.last_status.state}")
```

## 5. Get a Receipt

After confirmation, retrieve a formatted receipt:

```python
receipt = sdk.get_receipt(session.session_id)

print(receipt.tx_hash)             # Solana transaction hash
print(receipt.explorer_url)        # Link to Solana Explorer
print(receipt.confirmation_time_ms) # How fast it confirmed
```

## Complete Example

```python title="quickstart.py"
from solanaeasy import SolanaEasy
from solanaeasy.exceptions import WaitTimeout

sdk = SolanaEasy(api_key="sk_test_1234567890")

# Create
session = sdk.create_payment(
    amount=50.00,
    order_id="order_001",
    description="Nike Air Max Pulse",
)
print(f"Deposit to: {session.wallet_public_key}")

# Wait
try:
    status = sdk.wait_for_confirmation(
        session.session_id,
        timeout=300,
        on_update=lambda s: print(f"  → {s.state}: {s.human_message}"),
    )
    print(f"\n✓ Payment {status.state}!")
except WaitTimeout:
    print("Payment timed out.")
```

## Next Steps

- [Payment Sessions →](../concepts/sessions.md)
- [Webhooks →](../concepts/webhooks.md)
- [Full API Reference →](../reference/client.md)
