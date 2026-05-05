# Changelog

All notable changes to the SolanaEasy Python SDK.

## [0.1.0] — 2026-05-05

### Added

- **Core SDK**
    - `SolanaEasy` synchronous client
    - `AsyncSolanaEasy` asynchronous client
    - `create_payment()` with metadata support
    - `check_status()` with wallet address in response
    - `wait_for_confirmation()` with callback support
    - `list_payments()` with filtering and pagination
    - `cancel_session()` for pre-payment cancellation
    - `refund()` for confirmed payment refunds
    - `get_receipt()` with Solana Explorer links
    - `get_wallet_balance()` for real-time balance checks

- **Webhooks**
    - `register_webhook()` endpoint registration
    - `verify_webhook_signature()` HMAC-SHA256 verification
    - `process_webhook()` automatic handler dispatch
    - `@sdk.on()` decorator for event handlers
    - Replay attack protection (5-minute window)

- **Models**
    - `PaymentSession` with `wallet_public_key` and `metadata`
    - `PaymentStatus` with human-readable messages
    - `PaymentReceipt` with Explorer URL
    - `WebhookEvent` for webhook payloads
    - 7 payment states: CREATED, PENDING, CONFIRMED, FAILED, EXPIRED, CANCELLED, REFUNDED

- **Error Handling**
    - Structured exception hierarchy
    - Automatic HTTP error mapping
    - Exponential retry on transient failures
    - `WaitTimeout` with last known status

- **CLI**
    - `solanaeasy status` — check session status
    - `solanaeasy payments` — list payments with filters
    - `solanaeasy wait` — real-time polling

- **Infrastructure**
    - `py.typed` for mypy support
    - `llms.txt` for AI assistant integration
    - 3 working examples (quickstart, webhook, advanced)
    - Full MkDocs documentation site

- **Solana Integration**
    - Per-session wallet generation (`solders.Keypair`)
    - Real-time balance monitoring via Devnet RPC
    - SOL transfer support
    - Devnet airdrop with hackathon fallback
