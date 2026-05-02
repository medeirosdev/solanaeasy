"""
Testes do módulo de verificação de assinaturas de webhook.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pytest

from solanaeasy import SolanaEasy, WebhookEvent
from solanaeasy._internal.webhook import generate_signature, verify_signature
from solanaeasy.exceptions import SolanaEasyError, WebhookError

FAKE_SECRET = "whsec_test_1234567890abcdef"
FAKE_PAYLOAD = json.dumps({
    "event_type": "payment.confirmed",
    "session_id": "sess_abc123",
    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    "data": {
        "session_id": "sess_abc123",
        "state": "CONFIRMED",
        "human_message": "Pagamento confirmado em 2.3s",
        "tx_hash": "5KJp9Fx...",
        "confirmed_at": datetime.now(tz=timezone.utc).isoformat(),
        "confirmation_time_ms": 2300,
        "error_code": None,
    }
}).encode()


class TestGenerateSignature:
    def test_gera_formato_correto(self):
        sig = generate_signature(b"payload", "secret")
        assert sig.startswith("t=")
        assert ",v1=" in sig

    def test_timestamp_presente(self):
        now = int(time.time())
        sig = generate_signature(b"payload", "secret", timestamp=now)
        parts = dict(p.split("=", 1) for p in sig.split(","))
        assert int(parts["t"]) == now

    def test_assinaturas_diferentes_para_payloads_diferentes(self):
        sig1 = generate_signature(b"payload_a", "secret")
        sig2 = generate_signature(b"payload_b", "secret")
        assert sig1 != sig2

    def test_assinaturas_diferentes_para_secrets_diferentes(self):
        sig1 = generate_signature(b"payload", "secret_a")
        sig2 = generate_signature(b"payload", "secret_b")
        assert sig1 != sig2


class TestVerifySignature:
    def test_verifica_assinatura_valida(self):
        payload = b"test payload"
        sig = generate_signature(payload, FAKE_SECRET)
        assert verify_signature(payload, sig, FAKE_SECRET) is True

    def test_rejeita_payload_adulterado(self):
        payload = b"test payload"
        sig = generate_signature(payload, FAKE_SECRET)
        assert verify_signature(b"payload adulterado", sig, FAKE_SECRET) is False

    def test_rejeita_secret_errado(self):
        payload = b"test payload"
        sig = generate_signature(payload, FAKE_SECRET)
        assert verify_signature(payload, sig, "secret_errado") is False

    def test_rejeita_assinatura_expirada(self):
        payload = b"test payload"
        old_timestamp = int(time.time()) - 400  # 400s atrás, tolerance=300s
        sig = generate_signature(payload, FAKE_SECRET, timestamp=old_timestamp)
        assert verify_signature(payload, sig, FAKE_SECRET, tolerance=300) is False

    def test_aceita_dentro_da_tolerancia(self):
        payload = b"test payload"
        recent_timestamp = int(time.time()) - 60  # 60s atrás, tolerance=300s
        sig = generate_signature(payload, FAKE_SECRET, timestamp=recent_timestamp)
        assert verify_signature(payload, sig, FAKE_SECRET, tolerance=300) is True

    def test_rejeita_header_malformado(self):
        assert verify_signature(b"payload", "formato_invalido", FAKE_SECRET) is False

    def test_rejeita_header_vazio(self):
        assert verify_signature(b"payload", "", FAKE_SECRET) is False


class TestSdkVerifyWebhook:
    def _make_sdk(self):
        return SolanaEasy(
            api_key="sk_test_1234567890",
            base_url="http://fake.test",
            webhook_secret=FAKE_SECRET,
        )

    def test_verify_retorna_webhook_event(self):
        sdk = self._make_sdk()
        sig = generate_signature(FAKE_PAYLOAD, FAKE_SECRET)
        event = sdk.verify_webhook_signature(FAKE_PAYLOAD, sig)
        assert isinstance(event, WebhookEvent)
        assert event.event_type == "payment.confirmed"
        assert event.session_id == "sess_abc123"

    def test_verify_lanca_webhook_error_em_assinatura_invalida(self):
        sdk = self._make_sdk()
        with pytest.raises(WebhookError, match="inválida"):
            sdk.verify_webhook_signature(FAKE_PAYLOAD, "t=123,v1=assinatura_errada")

    def test_verify_lanca_erro_sem_webhook_secret(self):
        sdk = SolanaEasy(api_key="sk_test_1234567890", base_url="http://fake.test")
        with pytest.raises(SolanaEasyError, match="webhook_secret"):
            sdk.verify_webhook_signature(FAKE_PAYLOAD, "t=123,v1=abc")


class TestWebhookDecorator:
    def test_on_registra_handler(self):
        sdk = SolanaEasy(
            api_key="sk_test_1234567890",
            base_url="http://fake.test",
            webhook_secret=FAKE_SECRET,
        )
        received_events = []

        @sdk.on("payment.confirmed")
        def handle(event: WebhookEvent) -> None:
            received_events.append(event)

        sig = generate_signature(FAKE_PAYLOAD, FAKE_SECRET)
        sdk.process_webhook(FAKE_PAYLOAD, sig)

        assert len(received_events) == 1
        assert received_events[0].event_type == "payment.confirmed"

    def test_on_multiplos_handlers(self):
        sdk = SolanaEasy(
            api_key="sk_test_1234567890",
            base_url="http://fake.test",
            webhook_secret=FAKE_SECRET,
        )
        calls = []

        @sdk.on("payment.confirmed")
        def handler_a(event: WebhookEvent) -> None:
            calls.append("a")

        @sdk.on("payment.confirmed")
        def handler_b(event: WebhookEvent) -> None:
            calls.append("b")

        sig = generate_signature(FAKE_PAYLOAD, FAKE_SECRET)
        sdk.process_webhook(FAKE_PAYLOAD, sig)

        assert calls == ["a", "b"]

    def test_on_nao_chama_handler_de_outro_evento(self):
        sdk = SolanaEasy(
            api_key="sk_test_1234567890",
            base_url="http://fake.test",
            webhook_secret=FAKE_SECRET,
        )
        calls = []

        @sdk.on("payment.failed")  # evento diferente do payload
        def handler(event: WebhookEvent) -> None:
            calls.append("chamado")

        sig = generate_signature(FAKE_PAYLOAD, FAKE_SECRET)
        sdk.process_webhook(FAKE_PAYLOAD, sig)

        assert calls == []  # não foi chamado
