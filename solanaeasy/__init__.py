"""
SolanaEasy SDK para Python.

Uso básico (síncrono):
    from solanaeasy import SolanaEasy

    sdk = SolanaEasy(api_key="sk_test_...")
    session = sdk.create_payment(amount=50.00, order_id="pedido_123")
    status = sdk.check_status(session.session_id)

Uso assíncrono (FastAPI, asyncio):
    from solanaeasy import AsyncSolanaEasy

    async with AsyncSolanaEasy(api_key="sk_test_...") as sdk:
        session = await sdk.create_payment(amount=50.00, order_id="pedido_123")
        status = await sdk.wait_for_confirmation(session.session_id)
"""

from solanaeasy.async_client import AsyncSolanaEasy
from solanaeasy.client import SolanaEasy
from solanaeasy.exceptions import (
    AuthenticationError,
    InsufficientFunds,
    NetworkCongestion,
    PaymentError,
    RateLimitError,
    SessionNotFoundError,
    SolanaEasyError,
    TransactionExpired,
    WaitTimeout,
    WebhookError,
)
from solanaeasy.models import (
    PaymentReceipt,
    PaymentSession,
    PaymentState,
    PaymentStatus,
    WebhookEvent,
    WebhookEventType,
)

__version__ = "0.1.0"
__all__ = [
    # Clientes
    "SolanaEasy",
    "AsyncSolanaEasy",
    # Modelos
    "PaymentSession",
    "PaymentStatus",
    "WebhookEvent",
    "PaymentReceipt",
    "PaymentState",
    "WebhookEventType",
    # Exceções
    "SolanaEasyError",
    "AuthenticationError",
    "PaymentError",
    "InsufficientFunds",
    "TransactionExpired",
    "NetworkCongestion",
    "SessionNotFoundError",
    "WebhookError",
    "RateLimitError",
    "WaitTimeout",
]
