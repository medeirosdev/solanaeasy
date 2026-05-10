"""
SolanaEasy — Cliente principal do SDK.

Este é o único objeto que o desenvolvedor integrador precisa importar.

Uso básico:
    from solanaeasy import SolanaEasy

    sdk = SolanaEasy(api_key="sk_test_...")
    session = sdk.create_payment(amount=50.00, order_id="pedido_123")
    status = sdk.check_status(session.session_id)
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from typing import Any, Callable

from dotenv import load_dotenv

from solanaeasy._internal.http import HttpClient
from solanaeasy._internal.webhook import verify_signature
from solanaeasy.exceptions import SolanaEasyError, WaitTimeout, WebhookError
from solanaeasy.models import PaymentReceipt, PaymentSession, PaymentState, PaymentStatus, WebhookEvent

load_dotenv()

_DEFAULT_BASE_URL = "https://api.solanaeasy.dev"
_DEVNET_BASE_URL = "http://localhost:8000"
_VALID_NETWORKS = {"devnet", "mainnet-beta"}
_TERMINAL_STATES: set[PaymentState] = {"CONFIRMED", "FAILED", "EXPIRED"}


class SolanaEasy:
    """
    Cliente principal do SDK SolanaEasy.

    Parâmetros:
        api_key:        Chave de API gerada no dashboard. Lê SOLANAEASY_API_KEY se omitida.
        network:        "devnet" (padrão) ou "mainnet-beta".
        base_url:       URL base do backend. Lê SOLANAEASY_BASE_URL se omitida.
        timeout:        Timeout das requisições em segundos (padrão: 30).
        webhook_secret: Secret para verificar assinaturas de webhook (whsec_...).
                        Necessário para usar verify_webhook_signature() e process_webhook().

    Exemplo:
        sdk = SolanaEasy(api_key="sk_test_...", webhook_secret="whsec_...")

        @sdk.on("payment.confirmed")
        def on_confirmed(event):
            fulfill_order(event.session_id)
    """

    def __init__(
        self,
        api_key: str | None = None,
        network: str = "devnet",
        base_url: str | None = None,
        timeout: float = 30.0,
        webhook_secret: str | None = None,
    ) -> None:
        resolved_key = api_key or os.getenv("SOLANAEASY_API_KEY")
        if not resolved_key:
            raise SolanaEasyError(
                "API key não fornecida. Passe api_key= ou defina SOLANAEASY_API_KEY.",
                code="MISSING_API_KEY",
            )

        resolved_network = network or os.getenv("SOLANAEASY_NETWORK", "devnet")
        if resolved_network not in _VALID_NETWORKS:
            raise SolanaEasyError(
                f"Rede inválida: '{resolved_network}'. Use 'devnet' ou 'mainnet-beta'.",
                code="INVALID_NETWORK",
            )

        default_url = _DEVNET_BASE_URL if resolved_network == "devnet" else _DEFAULT_BASE_URL
        resolved_url = base_url or os.getenv("SOLANAEASY_BASE_URL") or default_url

        self._api_key = resolved_key
        self._network = resolved_network
        self._webhook_secret = webhook_secret or os.getenv("SOLANAEASY_WEBHOOK_SECRET")
        self._http = HttpClient(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=timeout,
        )
        # Registro interno de handlers para @sdk.on()
        self._handlers: dict[str, list[Callable[[WebhookEvent], None]]] = defaultdict(list)

    # ── Pagamentos ─────────────────────────────────────────────────────────────

    def create_payment(
        self,
        amount: float,
        order_id: str,
        currency: str = "USDC",
        description: str = "",
        expires_in: int = 900,
        idempotency_key: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> PaymentSession:
        """
        Cria uma nova sessão de pagamento.

        Parâmetros:
            amount:           Valor a cobrar (ex: 50.00), deve ser > 0.
            order_id:         ID do pedido no seu sistema.
            currency:         Moeda — USDC por padrão (stablecoin).
            description:      Descrição do produto/serviço (aparece no recibo).
            expires_in:       Segundos até a sessão expirar (padrão: 900 = 15 min).
            idempotency_key:  Chave única para evitar cobrança dupla em retries.
                              Chamadas repetidas com a mesma chave retornam a sessão original.
            metadata:         Dicionário de metadados customizados (ex: {"user_id": "123", "sku": "NIKE-001"}).
                              Armazenados no backend e devolvidos em check_status() e webhooks.

        Retorna:
            PaymentSession com session_id e payment_url.

        Exemplo:
            session = sdk.create_payment(
                amount=50.00,
                order_id="pedido_123",
                description="Tênis Nike Air Max",
                idempotency_key="pedido_123_v1",
                metadata={"user_id": "u_42", "sku": "NIKE-AM-001"},
            )
            redirect_user_to(session.payment_url)
        """
        if amount <= 0:
            raise SolanaEasyError("O valor deve ser maior que zero.", code="INVALID_AMOUNT")
        if not order_id.strip():
            raise SolanaEasyError("order_id não pode ser vazio.", code="INVALID_ORDER_ID")

        extra_headers = {}
        if idempotency_key:
            extra_headers["Idempotency-Key"] = idempotency_key

        body: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "order_id": order_id,
            "description": description,
            "expires_in": expires_in,
        }
        if metadata:
            body["metadata"] = metadata

        data = self._http.post(
            "/sessions",
            json=body,
            extra_headers=extra_headers or None,
        )
        return PaymentSession(**data)

    def check_status(self, session_id: str) -> PaymentStatus:
        """
        Verifica o status atual de uma sessão de pagamento.

        Parâmetros:
            session_id: ID da sessão retornado por create_payment().

        Retorna:
            PaymentStatus com state e human_message.

        Exemplo:
            status = sdk.check_status(session.session_id)
            if status.state == "CONFIRMED":
                fulfill_order(status.session_id)
        """
        if not session_id.strip():
            raise SolanaEasyError("session_id não pode ser vazio.", code="INVALID_SESSION_ID")

        data = self._http.get(f"/sessions/{session_id}")
        return PaymentStatus(**data)

    def wait_for_confirmation(
        self,
        session_id: str,
        timeout: int = 120,
        poll_interval: float = 2.0,
        on_update: Callable[[PaymentStatus], None] | None = None,
    ) -> PaymentStatus:
        """
        Bloqueia até o pagamento atingir um estado terminal (CONFIRMED, FAILED ou EXPIRED).

        Elimina a necessidade de escrever um loop de polling manualmente.

        Parâmetros:
            session_id:    ID da sessão a monitorar.
            timeout:       Segundos máximos de espera (padrão: 120).
            poll_interval: Intervalo entre verificações em segundos (padrão: 2.0).
            on_update:     Callback opcional chamado a cada mudança de estado.
                           Recebe o PaymentStatus atualizado.

        Retorna:
            PaymentStatus quando CONFIRMED, FAILED ou EXPIRED.

        Lança:
            WaitTimeout se o timeout for atingido sem estado terminal.
            WaitTimeout.last_status contém o último estado conhecido.

        Exemplo:
            try:
                status = sdk.wait_for_confirmation(
                    session.session_id,
                    timeout=120,
                    on_update=lambda s: print(f"Estado: {s.state}"),
                )
                print(status.human_message)
            except WaitTimeout as e:
                print(f"Ainda {e.last_status.state} após {e.timeout}s")
        """
        deadline = time.monotonic() + timeout
        last_status = self.check_status(session_id)

        if on_update:
            on_update(last_status)

        while last_status.state not in _TERMINAL_STATES:
            if time.monotonic() >= deadline:
                raise WaitTimeout(
                    session_id=session_id,
                    last_status=last_status,
                    timeout=timeout,
                )
            time.sleep(poll_interval)
            new_status = self.check_status(session_id)

            if on_update and new_status.state != last_status.state:
                on_update(new_status)

            last_status = new_status

        return last_status

    def list_payments(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PaymentSession]:
        """
        Lista os pagamentos do lojista com filtros opcionais.

        Parâmetros:
            status: Filtrar por estado ("CONFIRMED", "PENDING", etc.)
            limit:  Máximo de resultados (padrão: 20)
            offset: Paginação

        Retorna:
            Lista de PaymentSession
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        data = self._http.get("/sessions", params=params)
        return [PaymentSession(**item) for item in data.get("items", [])]

    def refund(self, session_id: str) -> PaymentStatus:
        """
        Inicia o processo de estorno de um pagamento confirmado.

        Somente sessões com state == "CONFIRMED" podem ser estornadas.
        A operação transfere os fundos de volta para a carteira do pagador.

        Parâmetros:
            session_id: ID da sessão confirmada.

        Retorna:
            PaymentStatus com state == "REFUNDED".

        Exemplo:
            status = sdk.refund("sess_abc123")
            print(status.human_message)  # "Refund processed."
        """
        if not session_id.strip():
            raise SolanaEasyError("session_id não pode ser vazio.", code="INVALID_SESSION_ID")
        data = self._http.post(f"/sessions/{session_id}/refund")
        return PaymentStatus(**data)

    def cancel_session(self, session_id: str) -> PaymentStatus:
        """
        Cancela uma sessão de pagamento antes que o cliente pague.

        Somente sessões com state == "CREATED" ou "PENDING" podem ser canceladas.
        Após o cancelamento, a sessão não aceita mais depósitos.

        Parâmetros:
            session_id: ID da sessão a cancelar.

        Retorna:
            PaymentStatus com state == "CANCELLED".

        Exemplo:
            status = sdk.cancel_session("sess_abc123")
            print(status.state)  # "CANCELLED"
        """
        if not session_id.strip():
            raise SolanaEasyError("session_id não pode ser vazio.", code="INVALID_SESSION_ID")
        data = self._http.post(f"/sessions/{session_id}/cancel")
        return PaymentStatus(**data)

    def get_receipt(self, session_id: str) -> PaymentReceipt:
        """
        Obtém o recibo detalhado de um pagamento confirmado.

        Disponível apenas para sessões com state == "CONFIRMED".
        Inclui tx_hash, explorer_url, tempo de confirmação e valor em BRL.

        Parâmetros:
            session_id: ID da sessão confirmada.

        Retorna:
            PaymentReceipt com todos os dados da transação.

        Exemplo:
            receipt = sdk.get_receipt("sess_abc123")
            print(receipt.explorer_url)   # Link para o Solana Explorer
            print(receipt.tx_hash)        # Hash da transação
        """
        if not session_id.strip():
            raise SolanaEasyError("session_id não pode ser vazio.", code="INVALID_SESSION_ID")
        data = self._http.get(f"/sessions/{session_id}/receipt")
        return PaymentReceipt(**data)

    def get_wallet_balance(self, session_id: str) -> dict[str, Any]:
        """
        Consulta o saldo atual da carteira Solana gerada para uma sessão.

        Útil para verificar se o depósito foi feito ou para debugging.

        Parâmetros:
            session_id: ID da sessão.

        Retorna:
            Dicionário com:
            - wallet_public_key (str): Endereço da carteira.
            - sol_balance (float): Saldo em SOL.
            - network (str): Rede (devnet ou mainnet-beta).

        Exemplo:
            info = sdk.get_wallet_balance("sess_abc123")
            print(f"Saldo: {info['sol_balance']} SOL")
        """
        if not session_id.strip():
            raise SolanaEasyError("session_id não pode ser vazio.", code="INVALID_SESSION_ID")
        return self._http.get(f"/sessions/{session_id}/balance")

    # ── Webhooks ───────────────────────────────────────────────────────────────

    def register_webhook(self, url: str) -> bool:
        """
        Registra uma URL para receber eventos de pagamento em tempo real.

        Parâmetros:
            url: URL HTTPS do seu endpoint.

        Eventos enviados:
            - payment.confirmed
            - payment.failed
            - payment.expired
            - payment.pending
        """
        if not url.startswith(("http://", "https://")):
            raise SolanaEasyError(
                "URL do webhook deve começar com http:// ou https://",
                code="INVALID_WEBHOOK_URL",
            )
        self._http.post("/webhooks", json={"url": url})
        return True

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> WebhookEvent:
        """
        Verifica a assinatura HMAC-SHA256 de um webhook e retorna o evento parseado.

        Garante que o payload veio de fato do servidor SolanaEasy.
        Protege contra replay attacks (rejeita assinaturas com mais de 5 min).

        Parâmetros:
            payload:   Corpo bruto da requisição (bytes).
            signature: Valor do header X-SolanaEasy-Signature.

        Retorna:
            WebhookEvent parseado e validado.

        Lança:
            WebhookError se a assinatura for inválida ou expirada.
            SolanaEasyError se webhook_secret não foi configurado.

        Exemplo:
            @app.post("/webhook/solana")
            def handle_webhook(request):
                event = sdk.verify_webhook_signature(
                    payload=request.body,
                    signature=request.headers["X-SolanaEasy-Signature"],
                )
                print(event.event_type)  # "payment.confirmed"
        """
        if not self._webhook_secret:
            raise SolanaEasyError(
                "webhook_secret não configurado. "
                "Passe webhook_secret= no construtor ou defina SOLANAEASY_WEBHOOK_SECRET.",
                code="MISSING_WEBHOOK_SECRET",
            )

        is_valid = verify_signature(
            payload=payload,
            signature_header=signature,
            secret=self._webhook_secret,
        )

        if not is_valid:
            raise WebhookError(
                "Assinatura do webhook inválida ou expirada. "
                "Verifique seu webhook_secret e o header X-SolanaEasy-Signature.",
                code="INVALID_WEBHOOK_SIGNATURE",
            )

        try:
            data = json.loads(payload)
            return WebhookEvent(**data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise WebhookError(
                f"Payload do webhook inválido: {exc}",
                code="INVALID_WEBHOOK_PAYLOAD",
            ) from exc

    def on(self, event_type: str) -> Callable:
        """
        Decorator para registrar handlers de eventos de webhook.

        Parâmetros:
            event_type: Tipo do evento a escutar.
                        Valores válidos: "payment.confirmed", "payment.failed",
                        "payment.expired", "payment.pending"

        Exemplo:
            @sdk.on("payment.confirmed")
            def handle_confirmed(event: WebhookEvent):
                fulfill_order(event.session_id)

            @sdk.on("payment.failed")
            def handle_failed(event: WebhookEvent):
                notify_customer(event.session_id)
        """
        def decorator(func: Callable[[WebhookEvent], None]) -> Callable[[WebhookEvent], None]:
            self._handlers[event_type].append(func)
            return func
        return decorator

    def process_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """
        Verifica a assinatura, parseia o evento e dispara os handlers registrados via @sdk.on().

        Use este método no seu endpoint de webhook para processar tudo de uma vez.

        Parâmetros:
            payload:   Corpo bruto da requisição (bytes).
            signature: Valor do header X-SolanaEasy-Signature.

        Retorna:
            WebhookEvent processado.

        Exemplo:
            @app.post("/webhook/solana")
            def webhook_endpoint(request):
                sdk.process_webhook(
                    payload=request.body,
                    signature=request.headers["X-SolanaEasy-Signature"],
                )
                return 200
        """
        event = self.verify_webhook_signature(payload, signature)
        for handler in self._handlers.get(event.event_type, []):
            handler(event)
        return event

    # ── Context Manager ────────────────────────────────────────────────────────

    def close(self) -> None:
        """Fecha o cliente HTTP. Chame ao finalizar o uso do SDK."""
        self._http.close()

    def __enter__(self) -> "SolanaEasy":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        key_preview = f"{self._api_key[:8]}..." if len(self._api_key) > 8 else "***"
        return f"SolanaEasy(api_key={key_preview!r}, network={self._network!r})"
