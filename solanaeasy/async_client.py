"""
SolanaEasy — Cliente assíncrono.

Mesma interface do SolanaEasy síncrono, mas com async/await.
Ideal para FastAPI, aiohttp, e qualquer codebase assíncrona.

Uso:
    from solanaeasy import AsyncSolanaEasy

    async with AsyncSolanaEasy(api_key="sk_...") as sdk:
        session = await sdk.create_payment(amount=50.00, order_id="pedido_123")
        status = await sdk.wait_for_confirmation(session.session_id)
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from typing import Any, Callable

from dotenv import load_dotenv

from solanaeasy._internal.async_http import AsyncHttpClient
from solanaeasy._internal.webhook import verify_signature
from solanaeasy.exceptions import SolanaEasyError, WaitTimeout, WebhookError
from solanaeasy.models import PaymentSession, PaymentState, PaymentStatus, WebhookEvent

load_dotenv()

_DEFAULT_BASE_URL = "https://api.solanaeasy.dev"
_DEVNET_BASE_URL = "http://localhost:8000"
_VALID_NETWORKS = {"devnet", "mainnet-beta"}
_TERMINAL_STATES: set[PaymentState] = {"CONFIRMED", "FAILED", "EXPIRED"}


class AsyncSolanaEasy:
    """
    Cliente assíncrono do SDK SolanaEasy.

    Mesma interface do SolanaEasy síncrono, mas com async/await.
    Use como context manager async para gerenciar o ciclo de vida da conexão.

    Exemplo:
        async with AsyncSolanaEasy(api_key="sk_...") as sdk:
            session = await sdk.create_payment(
                amount=50.00,
                order_id="pedido_123",
            )
            status = await sdk.wait_for_confirmation(session.session_id)
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
        self._http = AsyncHttpClient(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=timeout,
        )
        self._handlers: dict[str, list[Callable[[WebhookEvent], Any]]] = defaultdict(list)

    # ── Pagamentos ─────────────────────────────────────────────────────────────

    async def create_payment(
        self,
        amount: float,
        order_id: str,
        currency: str = "USDC",
        description: str = "",
        expires_in: int = 900,
        idempotency_key: str | None = None,
    ) -> PaymentSession:
        """Cria uma nova sessão de pagamento. Veja SolanaEasy.create_payment() para documentação."""
        if amount <= 0:
            raise SolanaEasyError("O valor deve ser maior que zero.", code="INVALID_AMOUNT")
        if not order_id.strip():
            raise SolanaEasyError("order_id não pode ser vazio.", code="INVALID_ORDER_ID")

        extra_headers = {}
        if idempotency_key:
            extra_headers["Idempotency-Key"] = idempotency_key

        data = await self._http.post(
            "/sessions",
            json={
                "amount": amount,
                "currency": currency,
                "order_id": order_id,
                "description": description,
                "expires_in": expires_in,
            },
            extra_headers=extra_headers or None,
        )
        return PaymentSession(**data)

    async def check_status(self, session_id: str) -> PaymentStatus:
        """Verifica o status atual de uma sessão. Veja SolanaEasy.check_status()."""
        if not session_id.strip():
            raise SolanaEasyError("session_id não pode ser vazio.", code="INVALID_SESSION_ID")
        data = await self._http.get(f"/sessions/{session_id}")
        return PaymentStatus(**data)

    async def wait_for_confirmation(
        self,
        session_id: str,
        timeout: int = 120,
        poll_interval: float = 2.0,
        on_update: Callable[[PaymentStatus], Any] | None = None,
    ) -> PaymentStatus:
        """
        Aguarda assincronamente até o pagamento atingir um estado terminal.

        Não bloqueia o event loop — usa asyncio.sleep() internamente.

        Exemplo:
            status = await sdk.wait_for_confirmation(
                session.session_id,
                timeout=120,
                on_update=lambda s: print(f"Estado: {s.state}"),
            )
        """
        deadline = asyncio.get_event_loop().time() + timeout
        last_status = await self.check_status(session_id)

        if on_update:
            result = on_update(last_status)
            if asyncio.iscoroutine(result):
                await result

        while last_status.state not in _TERMINAL_STATES:
            if asyncio.get_event_loop().time() >= deadline:
                raise WaitTimeout(
                    session_id=session_id,
                    last_status=last_status,
                    timeout=timeout,
                )
            await asyncio.sleep(poll_interval)
            new_status = await self.check_status(session_id)

            if on_update and new_status.state != last_status.state:
                result = on_update(new_status)
                if asyncio.iscoroutine(result):
                    await result

            last_status = new_status

        return last_status

    async def list_payments(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PaymentSession]:
        """Lista os pagamentos do lojista. Veja SolanaEasy.list_payments()."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        data = await self._http.get("/sessions", params=params)
        return [PaymentSession(**item) for item in data.get("items", [])]

    async def register_webhook(self, url: str) -> bool:
        """Registra URL de webhook. Veja SolanaEasy.register_webhook()."""
        if not url.startswith(("http://", "https://")):
            raise SolanaEasyError(
                "URL do webhook deve começar com http:// ou https://",
                code="INVALID_WEBHOOK_URL",
            )
        await self._http.post("/webhooks", json={"url": url})
        return True

    # ── Webhooks ───────────────────────────────────────────────────────────────

    def verify_webhook_signature(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verifica assinatura do webhook. Veja SolanaEasy.verify_webhook_signature()."""
        if not self._webhook_secret:
            raise SolanaEasyError(
                "webhook_secret não configurado.",
                code="MISSING_WEBHOOK_SECRET",
            )
        if not verify_signature(payload, signature, self._webhook_secret):
            raise WebhookError(
                "Assinatura do webhook inválida ou expirada.",
                code="INVALID_WEBHOOK_SIGNATURE",
            )
        try:
            data = json.loads(payload)
            return WebhookEvent(**data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise WebhookError(f"Payload inválido: {exc}", code="INVALID_WEBHOOK_PAYLOAD") from exc

    def on(self, event_type: str) -> Callable:
        """Decorator para registrar handlers async ou sync de webhook."""
        def decorator(func: Callable[[WebhookEvent], Any]) -> Callable[[WebhookEvent], Any]:
            self._handlers[event_type].append(func)
            return func
        return decorator

    async def process_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verifica assinatura e dispara handlers async registrados via @sdk.on()."""
        event = self.verify_webhook_signature(payload, signature)
        for handler in self._handlers.get(event.event_type, []):
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        return event

    # ── Context Manager ────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Fecha o cliente HTTP assíncrono."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncSolanaEasy":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        key_preview = f"{self._api_key[:8]}..." if len(self._api_key) > 8 else "***"
        return f"AsyncSolanaEasy(api_key={key_preview!r}, network={self._network!r})"
