"""
SolanaEasy — Exceções do SDK.

Hierarquia:
    SolanaEasyError
    ├── AuthenticationError
    ├── PaymentError
    │   ├── InsufficientFunds
    │   ├── TransactionExpired
    │   └── NetworkCongestion
    ├── SessionNotFoundError
    ├── WebhookError
    └── RateLimitError
"""


class SolanaEasyError(Exception):
    """Exceção base de todos os erros do SDK SolanaEasy."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code  # Código de erro interno para debugging

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# ── Autenticação ──────────────────────────────────────────────────────────────


class AuthenticationError(SolanaEasyError):
    """
    API key inválida ou ausente.

    Exemplo:
        sdk = SolanaEasy(api_key="chave_errada")
        # Lança AuthenticationError na primeira chamada
    """


# ── Erros de Pagamento ────────────────────────────────────────────────────────


class PaymentError(SolanaEasyError):
    """
    Erro genérico relacionado ao fluxo de pagamento.
    Especialize com as subclasses abaixo quando possível.
    """


class InsufficientFunds(PaymentError):
    """
    Carteira do cliente sem saldo suficiente para cobrir o pagamento.

    Erro on-chain original: 'insufficient funds for instruction'
    Mensagem humanizada: 'Saldo insuficiente na carteira do cliente'
    """


class TransactionExpired(PaymentError):
    """
    Blockhash da transação expirou antes de ser confirmado.

    Erro on-chain original: 'blockhash not found'
    Mensagem humanizada: 'Transação expirou, solicite novo pagamento'
    """


class NetworkCongestion(PaymentError):
    """
    Rede Solana congestionada — transação não processada a tempo.

    Erro on-chain original: 'transaction timeout'
    Mensagem humanizada: 'Rede congestionada, tente novamente'
    """


# ── Erros de Sessão ───────────────────────────────────────────────────────────


class WaitTimeout(SolanaEasyError):
    """
    wait_for_confirmation() atingiu o timeout sem o pagamento chegar a um estado terminal.

    Atributos:
        last_status: último PaymentStatus conhecido antes do timeout
        timeout: número de segundos que foi aguardado

    Exemplo:
        try:
            status = sdk.wait_for_confirmation(session_id, timeout=30)
        except WaitTimeout as e:
            print(f"Ainda {e.last_status.state} após {e.timeout}s")
    """

    def __init__(
        self,
        session_id: str,
        last_status: "PaymentStatus",  # type: ignore[name-defined]
        timeout: int,
    ) -> None:
        super().__init__(
            f"Timeout de {timeout}s atingido aguardando confirmação da sessão '{session_id}'.",
            code="WAIT_TIMEOUT",
        )
        self.last_status = last_status
        self.timeout = timeout


class SessionNotFoundError(SolanaEasyError):
    """
    session_id não encontrado no backend.

    Exemplo:
        sdk.check_status("sess_inexistente")
        # Lança SessionNotFoundError
    """


# ── Webhooks ──────────────────────────────────────────────────────────────────


class WebhookError(SolanaEasyError):
    """Falha ao registrar ou disparar webhook."""


# ── Rate Limit ────────────────────────────────────────────────────────────────


class RateLimitError(SolanaEasyError):
    """
    Muitas requisições em pouco tempo.
    Aguarde e tente novamente.
    """

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message, code="RATE_LIMIT")
        self.retry_after = retry_after  # segundos para esperar
