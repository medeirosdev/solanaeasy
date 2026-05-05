# Security

Security measures implemented across the SolanaEasy ecosystem.

## API Authentication

All API requests require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer sk_test_1234567890
```

The SDK handles this automatically when you provide `api_key` to the constructor.

!!! warning "Keep your API key secret"
    Never expose your API key in client-side code, public repositories, or logs.

## Wallet Isolation

Each payment session generates a **unique Solana keypair**. This provides:

- **Isolation**: Funds from different payments never mix
- **Traceability**: Each transaction maps to exactly one session
- **Security**: Compromising one wallet doesn't affect others

## Private Key Storage

Private keys are:

- Generated server-side using `solders.Keypair()` (cryptographically secure random)
- Stored in the backend database
- **Never exposed** via any API endpoint
- Used only internally for balance checks and (future) transfer operations

## Webhook Security

### HMAC-SHA256 Signatures

Every webhook payload is signed with your `webhook_secret`:

```
X-SolanaEasy-Signature: t=1234567890,v1=abc123...
```

The signature algorithm:

```python
signed_payload = f"{timestamp}.".encode() + raw_body
signature = HMAC-SHA256(webhook_secret, signed_payload)
```

### Replay Protection

Signatures include a timestamp. The SDK rejects any signature older than **5 minutes**, preventing replay attacks.

### Constant-Time Comparison

Signature verification uses `hmac.compare_digest()` to prevent timing attacks.

## HTTP Security

### Automatic Retries

The SDK retries on transient server errors (502, 503, 504) with exponential backoff, preventing data loss from network glitches.

### Timeout Protection

All HTTP requests have a configurable timeout (default: 30 seconds) to prevent hanging connections.

### Rate Limiting

The backend returns HTTP 429 with a `Retry-After` header when rate limits are exceeded. The SDK raises `RateLimitError` with the `retry_after` value.

## Idempotency

The `idempotency_key` parameter prevents duplicate charges on network retries:

```python
session = sdk.create_payment(
    amount=50.00,
    order_id="order_123",
    idempotency_key="order_123_v1",
)
```

Same key + same merchant = same session returned. No double charges.

## Best Practices

1. **Rotate API keys** periodically
2. **Use HTTPS** for webhook endpoints in production
3. **Always verify** webhook signatures before processing events
4. **Store session IDs** in your database for reconciliation
5. **Use idempotency keys** for all payment creation calls
6. **Monitor** the `/balance` endpoint during development to verify fund receipt
