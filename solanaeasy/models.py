"""
SolanaEasy — Modelos de dados públicos do SDK.

Estes são os tipos que o desenvolvedor recebe ao chamar os métodos do SDK.
Todos os modelos são imutáveis (frozen=True) para evitar modificação acidental.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

# Tipo dos estados possíveis de uma sessão de pagamento
PaymentState = Literal["CREATED", "PENDING", "CONFIRMED", "FAILED", "EXPIRED", "CANCELLED", "REFUNDED"]

# Tipo dos eventos de webhook
WebhookEventType = Literal[
    "payment.confirmed",
    "payment.failed",
    "payment.expired",
    "payment.pending",
]


class PaymentSession(BaseModel):
    """
    Sessão de pagamento criada pelo SDK.
    Retornada por SolanaEasy.create_payment().

    Exemplo de uso:
        session = sdk.create_payment(amount=50.00, ...)
        # Mostre session.payment_url para o cliente pagar
        # Guarde session.session_id para verificar status depois
    """

    model_config = {"frozen": True}

    session_id: str = Field(description="Identificador único da sessão")
    payment_url: str = Field(description="URL para o cliente realizar o pagamento")
    amount: float = Field(description="Valor a ser pago", gt=0)
    currency: str = Field(default="USDC", description="Moeda (USDC por padrão)")
    order_id: str = Field(description="ID do pedido no sistema do lojista")
    description: str = Field(default="", description="Descrição do produto/serviço")
    state: PaymentState = Field(default="CREATED", description="Estado atual da sessão")
    wallet_public_key: str | None = Field(
        default=None,
        description="Endereço da carteira Solana gerada para este pagamento",
    )
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Metadados customizados do lojista (ex: user_id, sku)",
    )
    created_at: datetime = Field(description="Data/hora de criação da sessão")
    expires_at: datetime = Field(description="Data/hora de expiração (default: +15min)")

    @property
    def is_expired(self) -> bool:
        """Retorna True se a sessão já passou do prazo de expiração."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_confirmed(self) -> bool:
        """Atalho para verificar se o pagamento foi confirmado."""
        return self.state == "CONFIRMED"


class PaymentStatus(BaseModel):
    """
    Status atual de uma sessão de pagamento.
    Retornado por SolanaEasy.check_status().

    Exemplo de uso:
        status = sdk.check_status(session.session_id)
        print(status.state)          # "CONFIRMED"
        print(status.human_message)  # "Pagamento confirmado em 2.3s"
    """

    model_config = {"frozen": True}

    session_id: str = Field(description="ID da sessão")
    state: PaymentState = Field(description="Estado atual")
    human_message: str = Field(
        description="Mensagem legível descrevendo o estado"
    )
    wallet_public_key: str | None = Field(
        default=None,
        description="Endereço da carteira Solana gerada para este pagamento",
    )

    # Disponíveis apenas quando state == "CONFIRMED"
    tx_hash: str | None = Field(
        default=None,
        description="Hash da transação na Solana (disponível após confirmação)",
    )
    confirmed_at: datetime | None = Field(
        default=None,
        description="Timestamp da confirmação",
    )
    confirmation_time_ms: int | None = Field(
        default=None,
        description="Tempo de confirmação em milissegundos",
    )

    # Disponível apenas quando state == "FAILED"
    error_code: str | None = Field(
        default=None,
        description="Código do erro on-chain (para debugging)",
    )


class WebhookEvent(BaseModel):
    """
    Evento enviado para o URL de webhook registrado pelo lojista.

    O body do POST que seu endpoint receberá será este modelo serializado em JSON.

    Exemplo de payload:
        {
            "event_type": "payment.confirmed",
            "session_id": "sess_abc123",
            "timestamp": "2024-01-01T14:32:01Z",
            "data": { ... PaymentStatus ... }
        }
    """

    model_config = {"frozen": True}

    event_type: WebhookEventType = Field(description="Tipo do evento")
    session_id: str = Field(description="ID da sessão relacionada")
    timestamp: datetime = Field(description="Momento em que o evento ocorreu")
    data: PaymentStatus = Field(description="Status completo da sessão no momento do evento")


class PaymentReceipt(BaseModel):
    """
    Recibo humanizado de um pagamento confirmado.
    Retornado pela API /sessions/:id/receipt e usado no Dashboard.
    """

    model_config = {"frozen": True}

    session_id: str
    order_id: str
    description: str
    amount: float
    currency: str
    amount_brl: float | None = Field(
        default=None,
        description="Equivalente em BRL (cotação no momento da confirmação)",
    )
    tx_hash: str
    block_number: int | None = None
    confirmed_at: datetime
    confirmation_time_ms: int | None = None
    explorer_url: str = Field(
        description="Link para ver a transação no Solana Explorer"
    )
