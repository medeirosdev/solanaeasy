"""
Testes da API pública do SolanaEasy SDK.
Cobre: create_payment, check_status, list_payments, register_webhook.
"""

from __future__ import annotations

import pytest
from httpx import Response

from solanaeasy import (
    SolanaEasy,
    AuthenticationError,
    SessionNotFoundError,
    RateLimitError,
    SolanaEasyError,
)
from solanaeasy.models import PaymentSession, PaymentStatus

from tests.conftest import (
    FAKE_API_KEY,
    FAKE_BASE_URL,
    FAKE_SESSION_ID,
    FAKE_SESSION_DATA,
    FAKE_STATUS_CONFIRMED,
    FAKE_STATUS_PENDING,
    FAKE_STATUS_FAILED,
)


# ── Construtor ────────────────────────────────────────────────────────────────


class TestSolanaEasyInit:
    def test_cria_sdk_com_api_key(self):
        sdk = SolanaEasy(api_key=FAKE_API_KEY, base_url=FAKE_BASE_URL)
        assert sdk is not None

    def test_lanca_erro_sem_api_key(self):
        with pytest.raises(SolanaEasyError, match="API key"):
            SolanaEasy(api_key=None)  # sem variável de ambiente

    def test_lanca_erro_rede_invalida(self):
        with pytest.raises(SolanaEasyError, match="Rede inválida"):
            SolanaEasy(api_key=FAKE_API_KEY, network="localnet")  # tipo: ignore

    def test_repr_nao_expoe_api_key_completa(self):
        sdk = SolanaEasy(api_key=FAKE_API_KEY, base_url=FAKE_BASE_URL)
        assert FAKE_API_KEY not in repr(sdk)
        assert "sk_test_" in repr(sdk)  # Mostra apenas o prefixo

    def test_context_manager(self):
        with SolanaEasy(api_key=FAKE_API_KEY, base_url=FAKE_BASE_URL) as sdk:
            assert sdk is not None


# ── create_payment ────────────────────────────────────────────────────────────


class TestCreatePayment:
    def test_retorna_payment_session(self, sdk, mock_api):
        mock_api.post("/sessions").mock(
            return_value=Response(200, json=FAKE_SESSION_DATA)
        )

        session = sdk.create_payment(amount=50.0, order_id="pedido_123")

        assert isinstance(session, PaymentSession)
        assert session.session_id == FAKE_SESSION_ID
        assert session.amount == 50.0
        assert session.state == "CREATED"

    def test_payment_url_existe(self, sdk, mock_api):
        mock_api.post("/sessions").mock(
            return_value=Response(200, json=FAKE_SESSION_DATA)
        )

        session = sdk.create_payment(amount=10.0, order_id="pedido_456")
        assert session.payment_url.startswith("https://")

    def test_lanca_erro_valor_zero(self, sdk):
        with pytest.raises(SolanaEasyError, match="maior que zero"):
            sdk.create_payment(amount=0, order_id="pedido_xyz")

    def test_lanca_erro_valor_negativo(self, sdk):
        with pytest.raises(SolanaEasyError, match="maior que zero"):
            sdk.create_payment(amount=-10.0, order_id="pedido_xyz")

    def test_lanca_erro_order_id_vazio(self, sdk):
        with pytest.raises(SolanaEasyError, match="order_id"):
            sdk.create_payment(amount=50.0, order_id="")

    def test_lanca_authentication_error_em_401(self, sdk, mock_api):
        mock_api.post("/sessions").mock(
            return_value=Response(401, json={"message": "Invalid API key"})
        )

        with pytest.raises(AuthenticationError):
            sdk.create_payment(amount=50.0, order_id="pedido_123")

    def test_lanca_rate_limit_error_em_429(self, sdk, mock_api):
        mock_api.post("/sessions").mock(
            return_value=Response(
                429,
                json={"message": "Too many requests"},
                headers={"Retry-After": "60"},
            )
        )

        with pytest.raises(RateLimitError) as exc_info:
            sdk.create_payment(amount=50.0, order_id="pedido_123")

        assert exc_info.value.retry_after == 60


# ── check_status ──────────────────────────────────────────────────────────────


class TestCheckStatus:
    def test_retorna_status_confirmado(self, sdk, mock_api):
        mock_api.get(f"/sessions/{FAKE_SESSION_ID}").mock(
            return_value=Response(200, json=FAKE_STATUS_CONFIRMED)
        )

        status = sdk.check_status(FAKE_SESSION_ID)

        assert isinstance(status, PaymentStatus)
        assert status.state == "CONFIRMED"
        assert status.tx_hash is not None
        assert "confirmado" in status.human_message.lower()

    def test_retorna_status_pendente(self, sdk, mock_api):
        mock_api.get(f"/sessions/{FAKE_SESSION_ID}").mock(
            return_value=Response(200, json=FAKE_STATUS_PENDING)
        )

        status = sdk.check_status(FAKE_SESSION_ID)
        assert status.state == "PENDING"
        assert status.tx_hash is None

    def test_retorna_status_falha(self, sdk, mock_api):
        mock_api.get(f"/sessions/{FAKE_SESSION_ID}").mock(
            return_value=Response(200, json=FAKE_STATUS_FAILED)
        )

        status = sdk.check_status(FAKE_SESSION_ID)
        assert status.state == "FAILED"
        assert status.error_code == "insufficient_funds"

    def test_lanca_session_not_found_em_404(self, sdk, mock_api):
        mock_api.get(f"/sessions/{FAKE_SESSION_ID}").mock(
            return_value=Response(404, json={"message": "Session not found"})
        )

        with pytest.raises(SessionNotFoundError):
            sdk.check_status(FAKE_SESSION_ID)

    def test_lanca_erro_session_id_vazio(self, sdk):
        with pytest.raises(SolanaEasyError, match="session_id"):
            sdk.check_status("")


# ── list_payments ─────────────────────────────────────────────────────────────


class TestListPayments:
    def test_retorna_lista_de_sessoes(self, sdk, mock_api):
        mock_api.get("/sessions").mock(
            return_value=Response(
                200,
                json={"items": [FAKE_SESSION_DATA, FAKE_SESSION_DATA], "total": 2},
            )
        )

        payments = sdk.list_payments()
        assert len(payments) == 2
        assert all(isinstance(p, PaymentSession) for p in payments)

    def test_lista_vazia(self, sdk, mock_api):
        mock_api.get("/sessions").mock(
            return_value=Response(200, json={"items": [], "total": 0})
        )

        payments = sdk.list_payments()
        assert payments == []


# ── register_webhook ──────────────────────────────────────────────────────────


class TestRegisterWebhook:
    def test_registra_webhook_com_sucesso(self, sdk, mock_api):
        mock_api.post("/webhooks").mock(
            return_value=Response(200, json={"registered": True})
        )

        result = sdk.register_webhook("https://meusite.com/webhook")
        assert result is True

    def test_lanca_erro_url_invalida(self, sdk):
        with pytest.raises(SolanaEasyError, match="http"):
            sdk.register_webhook("nao-e-uma-url")
