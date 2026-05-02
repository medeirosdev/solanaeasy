"""Testes para os modelos de dados do SDK."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from solanaeasy.models import PaymentSession, PaymentStatus, WebhookEvent


class TestPaymentSession:
    def _make_session(self, **kwargs) -> PaymentSession:
        base = {
            "session_id": "sess_test",
            "payment_url": "https://pay.solanaeasy.dev/sess_test",
            "amount": 50.0,
            "currency": "USDC",
            "order_id": "pedido_123",
            "description": "Produto teste",
            "state": "CREATED",
            "created_at": datetime.now(tz=timezone.utc),
            "expires_at": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
        }
        base.update(kwargs)
        return PaymentSession(**base)

    def test_cria_session_valida(self):
        session = self._make_session()
        assert session.session_id == "sess_test"
        assert session.state == "CREATED"

    def test_is_confirmed_falso_em_created(self):
        session = self._make_session(state="CREATED")
        assert session.is_confirmed is False

    def test_is_confirmed_verdadeiro(self):
        session = self._make_session(state="CONFIRMED")
        assert session.is_confirmed is True

    def test_is_expired_sessao_futura(self):
        session = self._make_session(
            expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1)
        )
        assert session.is_expired is False

    def test_sessao_e_imutavel(self):
        session = self._make_session()
        with pytest.raises(Exception):  # ValidationError ou AttributeError
            session.amount = 999.0  # type: ignore

    def test_lanca_erro_valor_zero(self):
        with pytest.raises(ValidationError):
            self._make_session(amount=0)

    def test_lanca_erro_valor_negativo(self):
        with pytest.raises(ValidationError):
            self._make_session(amount=-1.0)


class TestPaymentStatus:
    def test_status_confirmado_completo(self):
        status = PaymentStatus(
            session_id="sess_abc",
            state="CONFIRMED",
            human_message="Pagamento confirmado em 2.3s",
            tx_hash="5KJp9Fx...",
            confirmed_at=datetime.now(tz=timezone.utc),
            confirmation_time_ms=2300,
        )
        assert status.state == "CONFIRMED"
        assert status.tx_hash is not None

    def test_status_falha_tem_error_code(self):
        status = PaymentStatus(
            session_id="sess_abc",
            state="FAILED",
            human_message="Saldo insuficiente",
            error_code="insufficient_funds",
        )
        assert status.error_code == "insufficient_funds"
        assert status.tx_hash is None
