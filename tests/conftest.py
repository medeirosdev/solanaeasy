"""
Fixtures compartilhadas entre todos os testes do SDK SolanaEasy.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import respx
from httpx import Response

from solanaeasy import SolanaEasy


# ── Dados de teste ────────────────────────────────────────────────────────────

FAKE_API_KEY = "sk_test_1234567890abcdef"
FAKE_BASE_URL = "http://fake-api.solanaeasy.test"
FAKE_SESSION_ID = "sess_abc123456789"

FAKE_SESSION_DATA = {
    "session_id": FAKE_SESSION_ID,
    "payment_url": f"https://pay.solanaeasy.dev/{FAKE_SESSION_ID}",
    "amount": 50.0,
    "currency": "USDC",
    "order_id": "pedido_123",
    "description": "Tênis Nike Air Max",
    "state": "CREATED",
    "created_at": datetime.now(tz=timezone.utc).isoformat(),
    "expires_at": (datetime.now(tz=timezone.utc) + timedelta(minutes=15)).isoformat(),
}

FAKE_STATUS_CONFIRMED = {
    "session_id": FAKE_SESSION_ID,
    "state": "CONFIRMED",
    "human_message": "Pagamento confirmado em 2.3s",
    "tx_hash": "5KJp9FxG8N2mQy3vL7wHrTs4XZbE6VcAhMdRnPuWqIoYeKf",
    "confirmed_at": datetime.now(tz=timezone.utc).isoformat(),
    "confirmation_time_ms": 2300,
    "error_code": None,
}

FAKE_STATUS_PENDING = {
    "session_id": FAKE_SESSION_ID,
    "state": "PENDING",
    "human_message": "Aguardando confirmação na rede Solana...",
    "tx_hash": None,
    "confirmed_at": None,
    "confirmation_time_ms": None,
    "error_code": None,
}

FAKE_STATUS_FAILED = {
    "session_id": FAKE_SESSION_ID,
    "state": "FAILED",
    "human_message": "Saldo insuficiente na carteira do cliente",
    "tx_hash": None,
    "confirmed_at": None,
    "confirmation_time_ms": None,
    "error_code": "insufficient_funds",
}


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sdk() -> SolanaEasy:
    """SDK configurado para testes — usa URL falsa (sem chamadas reais)."""
    return SolanaEasy(
        api_key=FAKE_API_KEY,
        network="devnet",
        base_url=FAKE_BASE_URL,
    )


@pytest.fixture
def mock_api():
    """
    Contexto que intercepta todas as chamadas HTTP do SDK com respx.
    Uso:
        def test_algo(sdk, mock_api):
            mock_api.get("/sessions/sess_abc").mock(return_value=Response(200, json={...}))
    """
    with respx.mock(base_url=FAKE_BASE_URL) as api:
        yield api
