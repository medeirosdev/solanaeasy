"""
SolanaEasy — Wrapper interno para requisições HTTP.

Usa httpx com suporte a retry automático e mapeamento de erros HTTP
para as exceções do SDK.

NÃO é parte da API pública — use solanaeasy.client.SolanaEasy.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from solanaeasy.exceptions import (
    AuthenticationError,
    NetworkCongestion,
    RateLimitError,
    SessionNotFoundError,
    SolanaEasyError,
)

# Cabeçalho padrão enviado em todas as requisições
_SDK_VERSION = "0.1.0"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRY_STATUSES = {502, 503, 504}  # Erros de servidor que valem retry


class HttpClient:
    """
    Cliente HTTP interno do SDK.

    Responsável por:
    - Injetar api_key no cabeçalho Authorization
    - Converter erros HTTP em exceções do SDK
    - Retry automático em erros 5xx e timeout
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=self._default_headers(),
            timeout=timeout,
        )

    def _default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-SDK-Version": f"solanaeasy-python/{_SDK_VERSION}",
        }

    # ── Métodos públicos ────────────────────────────────────────────────────

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None, extra_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request("POST", path, json=json, extra_headers=extra_headers)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── Lógica interna ──────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        """Executa a requisição com retry em erros transitórios."""
        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                headers=extra_headers,
            )
        except httpx.TimeoutException:
            if attempt <= _MAX_RETRIES:
                self._wait_before_retry(attempt)
                return self._request(method, path, params, json, extra_headers, attempt + 1)
            raise NetworkCongestion(
                "Timeout na requisição — rede congestionada. Tente novamente.",
                code="REQUEST_TIMEOUT",
            )
        except httpx.RequestError as exc:
            raise SolanaEasyError(
                f"Erro de conexão com o servidor SolanaEasy: {exc}",
                code="CONNECTION_ERROR",
            ) from exc

        # Retry em erros de servidor transitórios
        if response.status_code in _RETRY_STATUSES and attempt <= _MAX_RETRIES:
            self._wait_before_retry(attempt)
            return self._request(
                method, path, params=params, json=json, extra_headers=extra_headers, attempt=attempt + 1
            )

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Converte erros HTTP em exceções do SDK."""
        if response.is_success:
            return response.json()

        # Tenta extrair mensagem de erro do corpo da resposta
        try:
            body = response.json()
            error_msg = body.get("message", response.text)
            error_code = body.get("code")
        except Exception:
            error_msg = response.text
            error_code = None

        status = response.status_code

        if status == 401:
            raise AuthenticationError(
                f"API key inválida ou expirada. {error_msg}",
                code="INVALID_API_KEY",
            )
        if status == 404:
            raise SessionNotFoundError(
                f"Recurso não encontrado. {error_msg}",
                code="NOT_FOUND",
            )
        if status == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Muitas requisições. Aguarde {retry_after}s antes de tentar novamente.",
                retry_after=retry_after,
            )

        raise SolanaEasyError(
            f"Erro inesperado do servidor (HTTP {status}): {error_msg}",
            code=error_code or f"HTTP_{status}",
        )

    @staticmethod
    def _wait_before_retry(attempt: int) -> None:
        """Espera exponencial entre tentativas: 1s, 2s, 4s..."""
        wait = 2 ** (attempt - 1)
        time.sleep(wait)
