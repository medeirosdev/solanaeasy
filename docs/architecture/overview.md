# Architecture Overview

How SolanaEasy abstracts blockchain complexity.

## System Architecture

```mermaid
graph TB
    subgraph Your Application
        A[Frontend] -->|API call| B[Your Backend]
    end

    subgraph SolanaEasy
        B -->|SDK| C[SolanaEasy SDK]
        C -->|HTTP/REST| D[SolanaEasy Backend]
        D -->|Webhook| B
    end

    subgraph Solana Network
        D -->|RPC| E[Solana Devnet/Mainnet]
        E -->|Confirmation| D
    end

    style C fill:#9945FF,color:#fff
    style D fill:#14F195,color:#000
    style E fill:#000,color:#14F195
```

## Request Flow

### 1. Payment Creation

```mermaid
sequenceDiagram
    participant App as Your App
    participant SDK as Python SDK
    participant API as SolanaEasy API
    participant Sol as Solana Network

    App->>SDK: create_payment(amount=50)
    SDK->>API: POST /sessions
    API->>API: Generate Keypair
    API->>API: Store in Database
    API-->>SDK: {session_id, wallet_public_key}
    SDK-->>App: PaymentSession object
```

### 2. Payment Monitoring

```mermaid
sequenceDiagram
    participant API as SolanaEasy API
    participant Sol as Solana Network
    participant DB as Database

    loop Every 10 seconds
        API->>Sol: getBalance(wallet)
        Sol-->>API: balance in lamports
        alt Balance > 0
            API->>DB: Update state → CONFIRMED
            API->>API: Fire webhooks
        end
    end
```

### 3. SDK Polling

```mermaid
sequenceDiagram
    participant App as Your App
    participant SDK as Python SDK
    participant API as SolanaEasy API

    App->>SDK: wait_for_confirmation()
    loop Every 2 seconds
        SDK->>API: GET /sessions/{id}
        API-->>SDK: {state: "CREATED"}
    end
    Note over SDK: State changes to CONFIRMED
    SDK->>API: GET /sessions/{id}
    API-->>SDK: {state: "CONFIRMED"}
    SDK-->>App: PaymentStatus (CONFIRMED)
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| **Python SDK** | HTTP client, polling, webhook verification, error translation |
| **FastAPI Backend** | Wallet generation, session management, Solana RPC, webhook delivery |
| **Solana Network** | Transaction processing, balance queries, on-chain finality |
| **SQLite Database** | Session persistence, state tracking, event history |

## Security Model

- API keys authenticate merchants via `Bearer` token
- Each payment session gets a **unique Solana keypair** — no shared wallets
- Private keys are stored encrypted in the database (never exposed via API)
- Webhook payloads are signed with HMAC-SHA256 and include replay protection
