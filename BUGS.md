# Relatório de Bugs e Melhorias (SolanaEasy SDK)

Este documento lista os bugs encontrados e melhorias propostas na revisão de código do pacote `solanaeasy-python`.

## 🚨 Bugs Críticos

### 1. Crash no Retry HTTP Síncrono (Positional Argument Mismatch)
- **Arquivo:** `solanaeasy/_internal/http.py`
- **Linha:** 119
- **Descrição:** Durante uma falha de conexão ou timeout (status 502, 503, 504), o método `_request` entra no bloco de *retry* e executa:
  ```python
  return self._request(method, path, params, json, attempt + 1)
  ```
  Como a assinatura real de `_request` é `(method, path, params=None, json=None, extra_headers=None, attempt=1)`, passar `attempt + 1` de forma posicional o injeta no parâmetro `extra_headers`. Isso causa um `TypeError` e o SDK irá falhar em vez de fazer a nova tentativa de conexão em rede corrompida.
- **Ação:** Refatorar a chamada do retry para usar argumentos explícitos (`extra_headers=extra_headers, attempt=attempt + 1`).

## ⚠️ Melhorias de Arquitetura e Lógica

### 2. URL Base do Devnet com Comportamento Inesperado
- **Arquivos:** `solanaeasy/client.py` e `solanaeasy/async_client.py`
- **Descrição:** A constante `_DEVNET_BASE_URL` está fixada em `http://localhost:8000`. Isso significa que, em produção, se um lojista usar apenas `network="devnet"`, o SDK vai tentar bater no `localhost` da máquina do próprio lojista.
- **Ação:** Alterar `_DEVNET_BASE_URL` para um endpoint real (`https://api.devnet.solanaeasy.dev`). Para testes de hackathon, criar uma network nova `"local"` ou documentar o uso explícito de `base_url="http://localhost:8000"`.

### 3. Deprecation Warning no Asyncio Loop
- **Arquivo:** `solanaeasy/async_client.py`
- **Linha:** Dentro de `wait_for_confirmation`
- **Descrição:** O código usa `asyncio.get_event_loop().time()` para o controle de timeout. No Python 3.10+, isso pode gerar warnings caso não haja um loop corrente explicito no contexto.
- **Ação:** Substituir por `asyncio.get_running_loop().time()`, que é a forma moderna e idiomática de lidar com clocks de corrotinas.

## ✍️ Developer Experience (DX) e Typos

### 4. Perda de Paridade em Docstrings (Async vs Sync)
- **Arquivo:** `solanaeasy/async_client.py`
- **Descrição:** O cliente assíncrono abstrai as documentações com apontamentos curtos (ex: `"""Veja SolanaEasy.create_payment() para documentacao."""`). Isso prejudica a experiência em IDEs como VSCode, pois o tooltip de hover para quem usa async/await aparece vazio.
- **Ação:** Replicar as *docstrings* e *type hints* literais e ricas do `client.py` direto nos métodos assíncronos.

### 5. Typos de Ortografia
- **Arquivo:** `solanaeasy/async_client.py`
- **Descrição:** No método `create_payment`, a validação de erro lança: `"order_id nao pode ser vazio."` (sem til). Em `client.py` a string está correta.
- **Ação:** Padronizar as mensagens de erro nos dois clientes e adicionar os acentos ausentes.
