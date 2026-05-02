"""
SolanaEasy — Cliente HTTP assíncrono interno.

Versão async do http.py, usa httpx.AsyncClient.
NÃO é parte da API pública.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from solanaeasy.exceptions import (
    AuthenticationError,
    NetworkCongestion,
    RateLimitError,
    SessionNotFoundError,
    SolanaEasyError,
)

_SDK_VERSION = "0.1.0"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRY_STATUSES = {502, 503, 504}


class AsyncHttpClient:
    """Cliente HTTP assíncrono interno do SDK."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(
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

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None, extra_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json=json, extra_headers=extra_headers)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        try:
            response = await self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                headers=extra_headers,
            )
        except httpx.TimeoutException:
            if attempt <= _MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt - 1))
                return await self._request(method, path, params, json, extra_headers, attempt + 1)
            raise NetworkCongestion(
                "Timeout na requisição — rede congestionada. Tente novamente.",
                code="REQUEST_TIMEOUT",
            )
        except httpx.RequestError as exc:
            raise SolanaEasyError(
                f"Erro de conexão: {exc}", code="CONNECTION_ERROR"
            ) from exc

        if response.status_code in _RETRY_STATUSES and attempt <= _MAX_RETRIES:
            await asyncio.sleep(2 ** (attempt - 1))
            return await self._request(method, path, params, json, extra_headers, attempt + 1)

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.is_success:
            return response.json()

        try:
            body = response.json()
            error_msg = body.get("message", response.text)
            error_code = body.get("code")
        except Exception:
            error_msg = response.text
            error_code = None

        status = response.status_code

        if status == 401:
            raise AuthenticationError(f"API key inválida. {error_msg}", code="INVALID_API_KEY")
        if status == 404:
            raise SessionNotFoundError(f"Recurso não encontrado. {error_msg}", code="NOT_FOUND")
        if status == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Muitas requisições. Aguarde {retry_after}s.",
                retry_after=retry_after,
            )
        raise SolanaEasyError(
            f"Erro do servidor (HTTP {status}): {error_msg}",
            code=error_code or f"HTTP_{status}",
        )
