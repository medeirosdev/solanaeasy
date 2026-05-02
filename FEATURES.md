# SolanaEasy Python SDK — Funcionalidades

> Documento vivo. Atualizado a cada nova feature implementada.
> Última atualização: 2026-05-02

---

## Status das Features

| Feature | Status | Módulo |
|---|---|---|
| `create_payment()` | ✅ Implementado | `client.py` |
| `check_status()` | ✅ Implementado | `client.py` |
| `list_payments()` | ✅ Implementado | `client.py` |
| `register_webhook()` | ✅ Implementado | `client.py` |
| `refund()` | 🔜 Fase 4 | `client.py` |
| `wait_for_confirmation()` | ✅ Implementado | `client.py` |
| Verificação de assinatura de webhook | ✅ Implementado | `client.py` + `_internal/webhook.py` |
| Idempotency key | ✅ Implementado | `client.py` |
| `@sdk.on()` decorator de webhook | ✅ Implementado | `client.py` |
| `AsyncSolanaEasy` | ✅ Implementado | `async_client.py` |
| CLI (`solanaeasy status`, `solanaeasy payments`) | ✅ Implementado | `cli.py` |
| `py.typed` (suporte mypy completo) | ✅ Implementado | `py.typed` |

---

## Detalhes das Features

---

### ✅ `create_payment()` — Criar sessão de pagamento

```python
session = sdk.create_payment(
    amount=50.00,
    currency="USDC",
    order_id="pedido_123",
    description="Tênis Nike Air Max",
    idempotency_key="pedido_123_v1",  # ← previne duplicatas
)
print(session.payment_url)   # URL para o cliente pagar
print(session.session_id)    # ID para rastrear depois
```

**Parâmetros:**
- `amount` (float, obrigatório) — valor a cobrar, deve ser > 0
- `currency` (str, padrão `"USDC"`) — moeda stablecoin
- `order_id` (str, obrigatório) — ID do pedido no sistema do lojista
- `description` (str, opcional) — aparece no recibo
- `expires_in` (int, padrão `900`) — segundos até expirar
- `idempotency_key` (str, opcional) — chave única para evitar cobrança dupla em retry

**Retorna:** `PaymentSession`

---

### ✅ `check_status()` — Verificar status

```python
status = sdk.check_status(session.session_id)
print(status.state)          # "PENDING" | "CONFIRMED" | "FAILED" | "EXPIRED"
print(status.human_message)  # "Pagamento confirmado em 2.3s"
print(status.tx_hash)        # hash da transação (se confirmada)
```

**Retorna:** `PaymentStatus`

---

### ✅ `wait_for_confirmation()` — Aguardar confirmação

Bloqueia até o pagamento ser confirmado, falhar ou expirar. Elimina a necessidade do dev fazer polling manual.

```python
try:
    status = sdk.wait_for_confirmation(
        session.session_id,
        timeout=120,
        poll_interval=2.0,
        on_update=lambda s: print(f"Estado: {s.state}"),
    )
    print(status.human_message)  # "Pagamento confirmado em 2.3s"

except WaitTimeout as e:
    print(f"Timeout! Último estado: {e.last_status.state}")
```

**Estados terminais:** `CONFIRMED`, `FAILED`, `EXPIRED`
**Lança:** `WaitTimeout` se o `timeout` for atingido

---

### ✅ Idempotency Key — Prevenir pagamento duplicado

Chamadas repetidas com a mesma chave retornam a sessão já criada.

```python
for _ in range(2):
    session = sdk.create_payment(
        amount=50.00,
        order_id="pedido_123",
        idempotency_key="pedido_123_attempt_1",
    )
# session.session_id é o mesmo nas duas chamadas
```

Enviado como header HTTP: `Idempotency-Key: pedido_123_attempt_1`

---

### ✅ Verificação de Assinatura de Webhook

Garante que o payload veio do servidor SolanaEasy (proteção contra replay attacks e spoofing).

```python
sdk = SolanaEasy(api_key="sk_...", webhook_secret="whsec_...")

@app.post("/webhook/solana")
def handle_webhook(request):
    try:
        event = sdk.verify_webhook_signature(
            payload=request.body,
            signature=request.headers["X-SolanaEasy-Signature"],
        )
        print(event.event_type)  # "payment.confirmed"
    except WebhookError:
        return 400
```

**Algoritmo:** HMAC-SHA256 com timestamp (previne replay attacks de até 5 min)
**Header:** `X-SolanaEasy-Signature: t=1234567890,v1=abc123...`

---

### ✅ `@sdk.on()` — Decorator de Webhook

Forma declarativa de registrar handlers para eventos específicos.

```python
sdk = SolanaEasy(api_key="sk_...", webhook_secret="whsec_...")

@sdk.on("payment.confirmed")
def pagamento_confirmado(event: WebhookEvent):
    fulfill_order(event.session_id)

@sdk.on("payment.failed")
def pagamento_falhou(event: WebhookEvent):
    notify_customer(event.session_id, event.data.human_message)

@app.post("/webhook/solana")
def webhook_endpoint(request):
    sdk.process_webhook(
        payload=request.body,
        signature=request.headers["X-SolanaEasy-Signature"],
    )
    return 200
```

---

### ✅ `AsyncSolanaEasy` — Cliente Assíncrono

Mesma interface do `SolanaEasy`, mas com `async/await`. Ideal para FastAPI.

```python
from solanaeasy import AsyncSolanaEasy

async def processar_pedido():
    async with AsyncSolanaEasy(api_key="sk_...") as sdk:
        session = await sdk.create_payment(amount=50.00, order_id="pedido_123")
        status = await sdk.wait_for_confirmation(session.session_id, timeout=120)
        return status
```

---

### ✅ CLI — Interface de Linha de Comando

```bash
# Verificar status de um pagamento
$ solanaeasy status sess_abc123

# Listar pagamentos recentes
$ solanaeasy payments --limit 5
$ solanaeasy payments --status CONFIRMED

# Aguardar confirmação em tempo real (polling visual)
$ solanaeasy wait sess_abc123

# Ajuda
$ solanaeasy --help
```

---

## Modelos de Dados

### `PaymentSession`
| Campo | Tipo | Descrição |
|---|---|---|
| `session_id` | `str` | ID único da sessão |
| `payment_url` | `str` | URL para o cliente pagar |
| `amount` | `float` | Valor cobrado (> 0) |
| `currency` | `str` | Moeda (padrão: USDC) |
| `order_id` | `str` | ID do pedido no sistema do lojista |
| `description` | `str` | Descrição do produto |
| `state` | `PaymentState` | Estado atual |
| `created_at` | `datetime` | Data de criação |
| `expires_at` | `datetime` | Data de expiração |
| `is_confirmed` | `bool` (property) | Atalho: state == CONFIRMED |
| `is_expired` | `bool` (property) | Atalho: passou do expires_at |

### `PaymentStatus`
| Campo | Tipo | Descrição |
|---|---|---|
| `session_id` | `str` | ID da sessão |
| `state` | `PaymentState` | Estado atual |
| `human_message` | `str` | Mensagem legível |
| `tx_hash` | `str or None` | Hash Solana (se confirmado) |
| `confirmed_at` | `datetime or None` | Timestamp da confirmação |
| `confirmation_time_ms` | `int or None` | Tempo de confirmação em ms |
| `error_code` | `str or None` | Código do erro on-chain (se falhou) |

---

## Exceções

| Exceção | Quando ocorre |
|---|---|
| `SolanaEasyError` | Base de todos os erros |
| `AuthenticationError` | API key inválida ou ausente |
| `PaymentError` | Erro genérico no fluxo de pagamento |
| `InsufficientFunds` | Saldo insuficiente na carteira do cliente |
| `TransactionExpired` | Blockhash expirou antes de confirmar |
| `NetworkCongestion` | Rede Solana congestionada |
| `SessionNotFoundError` | session_id não encontrado |
| `WebhookError` | Assinatura inválida ou falha no webhook |
| `RateLimitError` | Muitas requisições (tem `.retry_after`) |
| `WaitTimeout` | `wait_for_confirmation()` atingiu o timeout (tem `.last_status`) |

---

## Roadmap

### Fase 3 — Motor Solana (próxima)
- [ ] `_internal/solana/wallet.py` — geração de keypairs temporários por sessão
- [ ] `_internal/solana/rpc.py` — monitorar transações via WebSocket RPC
- [ ] `_internal/solana/tx_builder.py` — construção de transferências USDC

### Fase 4 — Polish
- [ ] `refund(session_id)` — estorno on-chain
- [ ] `_internal/translator.py` — mapeamento completo de erros Solana → linguagem humana
- [ ] Publicação no PyPI
