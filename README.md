# SolanaEasy Python SDK

> Integre pagamentos Solana em menos de 10 linhas. Sem saber que é blockchain.

```python
from solanaeasy import SolanaEasy

sdk = SolanaEasy(api_key="sk_test_...")

session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="pedido_123",
    description="Tênis Nike Air Max",
)

print(session.payment_url)  # → mostre esse link para o cliente pagar

status = sdk.check_status(session.session_id)
print(status.human_message)  # → "Pagamento confirmado em 2.3s"
```

---

## Instalação

```bash
pip install solanaeasy
```

## Métodos

| Método | O que faz |
|---|---|
| `create_payment(amount, currency, order_id, description)` | Cria sessão, retorna URL de pagamento |
| `check_status(session_id)` | Retorna estado + mensagem humana |
| `list_payments(status, limit, offset)` | Lista pagamentos com filtros |
| `register_webhook(url)` | Registra URL para receber notificações |
| `refund(session_id)` | Inicia estorno |

## Estados de uma Transação

| Estado | Significado |
|---|---|
| `CREATED` | Sessão criada, aguardando o cliente |
| `PENDING` | Cliente abriu o link, pagamento em andamento |
| `CONFIRMED` | Transação confirmada na Solana ✅ |
| `FAILED` | Falha (saldo, rede, etc.) ❌ |
| `EXPIRED` | 15 minutos sem pagamento ⏰ |

## Tratamento de Erros

```python
from solanaeasy import SolanaEasy
from solanaeasy.exceptions import InsufficientFunds, SessionNotFoundError

sdk = SolanaEasy(api_key="sk_test_...")

try:
    status = sdk.check_status("session_abc")
except SessionNotFoundError:
    print("Sessão não encontrada")
except InsufficientFunds:
    print("Cliente sem saldo suficiente")
```

## Webhooks

```python
sdk.register_webhook(url="https://meusite.com/webhook/solana")

# Seu endpoint receberá eventos como:
# {
#   "event_type": "payment.confirmed",
#   "session_id": "sess_abc123",
#   "data": { "state": "CONFIRMED", "human_message": "Pagamento confirmado em 2.3s" }
# }
```

## Variáveis de Ambiente

```bash
SOLANAEASY_API_KEY=sk_test_...
SOLANAEASY_NETWORK=devnet        # devnet | mainnet-beta
SOLANAEASY_BASE_URL=http://localhost:8000
```
