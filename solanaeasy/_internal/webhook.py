"""
SolanaEasy — Verificação de assinatura de webhooks.

Algoritmo: HMAC-SHA256 com timestamp (mesmo padrão do Stripe).
Formato do header: X-SolanaEasy-Signature: t=<timestamp>,v1=<hex_signature>

Proteção contra replay attacks: rejeita assinaturas com timestamp
mais de `tolerance` segundos no passado (padrão: 300s = 5 min).

NÃO é parte da API pública — use SolanaEasy.verify_webhook_signature().
"""

from __future__ import annotations

import hashlib
import hmac
import time

_HEADER_NAME = "X-SolanaEasy-Signature"
_DEFAULT_TOLERANCE = 300  # 5 minutos


def generate_signature(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    """
    Gera uma assinatura HMAC-SHA256 para o payload do webhook.
    Usado pelo backend ao enviar o evento.

    Retorna a string completa do header:
        "t=1234567890,v1=abc123..."
    """
    if timestamp is None:
        timestamp = int(time.time())

    signed_payload = f"{timestamp}.".encode() + payload
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return f"t={timestamp},v1={signature}"


def verify_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
    tolerance: int = _DEFAULT_TOLERANCE,
) -> bool:
    """
    Verifica se a assinatura do webhook é válida.

    Parâmetros:
        payload:          Corpo bruto da requisição (bytes)
        signature_header: Valor do header X-SolanaEasy-Signature
        secret:           Webhook secret configurado no SDK (whsec_...)
        tolerance:        Janela de tempo aceitável em segundos (default: 300)

    Retorna:
        True se válida, False se inválida ou expirada
    """
    try:
        parts = dict(item.split("=", 1) for item in signature_header.split(","))
        timestamp = int(parts["t"])
        expected_sig = parts["v1"]
    except (KeyError, ValueError):
        return False

    # Verifica se o timestamp está dentro da janela de tolerância
    now = int(time.time())
    if abs(now - timestamp) > tolerance:
        return False

    # Recalcula a assinatura e compara de forma segura (constant-time)
    signed_payload = f"{timestamp}.".encode() + payload
    computed = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, expected_sig)
