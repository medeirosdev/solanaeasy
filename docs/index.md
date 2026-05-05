---
hide:
  - navigation
---

# SolanaEasy Python SDK

<div style="text-align: center; margin: 2rem 0;">
<p style="font-size: 1.4rem; color: #9945FF;">The Stripe for Solana</p>
<p style="font-size: 1.1rem; opacity: 0.8;">Accept blockchain payments without knowing blockchain.<br>4 lines of code. Zero crypto knowledge required.</p>
</div>

---

## Why SolanaEasy?

| Traditional Solana Integration | With SolanaEasy |
|---|---|
| Manage RPC connections | `sdk.create_payment(amount=50.00)` |
| Generate and secure keypairs | Automatic per-session wallets |
| Build and sign transactions | Handled server-side |
| Parse on-chain errors | `status.human_message` |
| Monitor transaction finality | `sdk.wait_for_confirmation()` |
| Implement webhook security | HMAC-SHA256 built-in |

## Quick Example

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(api_key="sk_test_...")

# Create a payment — that's it
session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="order_123",
    description="Nike Air Max",
)

# Wait for the customer to pay
status = sdk.wait_for_confirmation(session.session_id)
print(status.human_message)  # "Payment confirmed on the Solana Devnet."
```

## Features

<div class="grid cards" markdown>

-   :material-lightning-bolt:{ .lg .middle } **Simple API**

    ---

    Create payments, check status, and handle webhooks with familiar HTTP concepts. No blockchain knowledge needed.

-   :material-shield-check:{ .lg .middle } **Secure by Default**

    ---

    HMAC-SHA256 webhook signatures, replay attack protection, and isolated per-session wallets.

-   :material-sync:{ .lg .middle } **Sync & Async**

    ---

    Both `SolanaEasy` and `AsyncSolanaEasy` share the same interface. Use whichever fits your stack.

-   :material-console:{ .lg .middle } **CLI Included**

    ---

    Inspect payments, check status, and wait for confirmations directly from the terminal.

-   :material-webhook:{ .lg .middle } **Webhooks**

    ---

    Real-time event delivery with `@sdk.on("payment.confirmed")` decorator pattern.

-   :material-undo:{ .lg .middle } **Refunds & Cancellations**

    ---

    Cancel pending sessions or refund confirmed payments with a single method call.

</div>

## Installation

```bash
pip install solanaeasy
```

[:material-arrow-right: Get Started](getting-started/installation.md){ .md-button .md-button--primary }
[:material-book-open-variant: API Reference](reference/client.md){ .md-button }
