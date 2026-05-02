"""
Testes de wait_for_confirmation() — síncrono e com timeout.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from solanaeasy import SolanaEasy
from solanaeasy.exceptions import WaitTimeout
from solanaeasy.models import PaymentStatus

FAKE_BASE_URL = "http://fake-api.solanaeasy.test"
FAKE_API_KEY = "sk_test_1234567890abcdef"
FAKE_SESSION_ID = "sess_wait_test"


def _make_status(state: str) -> PaymentStatus:
    return PaymentStatus(
        session_id=FAKE_SESSION_ID,
        state=state,  # type: ignore[arg-type]
        human_message=f"Estado: {state}",
        tx_hash="5KJp9Fx..." if state == "CONFIRMED" else None,
    )


def _make_sdk() -> SolanaEasy:
    return SolanaEasy(api_key=FAKE_API_KEY, base_url=FAKE_BASE_URL)


class TestWaitForConfirmation:
    def test_retorna_imediatamente_se_ja_confirmado(self):
        sdk = _make_sdk()
        confirmed = _make_status("CONFIRMED")

        with patch.object(sdk, "check_status", return_value=confirmed):
            result = sdk.wait_for_confirmation(FAKE_SESSION_ID, timeout=10)

        assert result.state == "CONFIRMED"

    def test_retorna_apos_uma_iteracao(self):
        sdk = _make_sdk()
        # Primeira chamada: PENDING; segunda: CONFIRMED
        pending = _make_status("PENDING")
        confirmed = _make_status("CONFIRMED")

        with patch.object(sdk, "check_status", side_effect=[pending, confirmed]):
            with patch("time.sleep"):  # evita espera real
                result = sdk.wait_for_confirmation(FAKE_SESSION_ID, timeout=30)

        assert result.state == "CONFIRMED"

    def test_retorna_em_estado_failed(self):
        sdk = _make_sdk()
        failed = _make_status("FAILED")

        with patch.object(sdk, "check_status", return_value=failed):
            result = sdk.wait_for_confirmation(FAKE_SESSION_ID, timeout=10)

        assert result.state == "FAILED"

    def test_retorna_em_estado_expired(self):
        sdk = _make_sdk()
        expired = _make_status("EXPIRED")

        with patch.object(sdk, "check_status", return_value=expired):
            result = sdk.wait_for_confirmation(FAKE_SESSION_ID, timeout=10)

        assert result.state == "EXPIRED"

    def test_lanca_wait_timeout_quando_excede_prazo(self):
        sdk = _make_sdk()
        pending = _make_status("PENDING")

        # Simula sempre retornar PENDING e o tempo passando
        with patch.object(sdk, "check_status", return_value=pending):
            with patch("time.sleep"):
                with patch("time.monotonic", side_effect=[0, 0, 200]):  # deadline de 10s, mas já em 200
                    with pytest.raises(WaitTimeout) as exc_info:
                        sdk.wait_for_confirmation(FAKE_SESSION_ID, timeout=10)

        assert exc_info.value.last_status.state == "PENDING"
        assert exc_info.value.timeout == 10

    def test_on_update_chamado_na_mudanca_de_estado(self):
        sdk = _make_sdk()
        pending = _make_status("PENDING")
        confirmed = _make_status("CONFIRMED")
        updates: list[str] = []

        def on_update(s: PaymentStatus) -> None:
            updates.append(s.state)

        with patch.object(sdk, "check_status", side_effect=[pending, confirmed]):
            with patch("time.sleep"):
                sdk.wait_for_confirmation(
                    FAKE_SESSION_ID,
                    timeout=30,
                    on_update=on_update,
                )

        # Chamado no estado inicial (PENDING) e na mudança para CONFIRMED
        assert "PENDING" in updates
        assert "CONFIRMED" in updates

    def test_wait_timeout_tem_last_status(self):
        sdk = _make_sdk()
        pending = _make_status("PENDING")

        with patch.object(sdk, "check_status", return_value=pending):
            with patch("time.sleep"):
                with patch("time.monotonic", side_effect=[0, 0, 9999]):
                    try:
                        sdk.wait_for_confirmation(FAKE_SESSION_ID, timeout=5)
                    except WaitTimeout as e:
                        assert isinstance(e.last_status, PaymentStatus)
                        assert e.last_status.state == "PENDING"
