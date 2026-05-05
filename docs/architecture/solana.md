# Solana Integration

How SolanaEasy interacts with the Solana blockchain under the hood.

## Network Support

| Network | Status | RPC Endpoint |
|---|---|---|
| Devnet | **Active** | `https://api.devnet.solana.com` |
| Mainnet-Beta | Planned | `https://api.mainnet-beta.solana.com` |

## Wallet Generation

Each payment session receives a unique Solana keypair:

```python
# Internal implementation (simplified)
from solders.keypair import Keypair

keypair = Keypair()  # Random Ed25519 keypair
public_key = str(keypair.pubkey())   # Deposit address
private_key = base58.b58encode(bytes(keypair))  # Stored securely
```

The public key is returned as `wallet_public_key` in the session response. The private key is stored in the database and never exposed via the API.

## Balance Monitoring

The backend runs a background worker that periodically checks wallet balances:

```python
# Simplified flow
async def monitor_sessions():
    while True:
        sessions = get_pending_sessions()
        for session in sessions:
            balance = await check_sol_balance(session.wallet_public_key)
            if balance > 0:
                confirm_session(session)
        await asyncio.sleep(10)
```

## Solana Constants

| Constant | Value |
|---|---|
| Lamports per SOL | 1,000,000,000 |
| USDC Devnet Mint | `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU` |
| USDC Mainnet Mint | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |

## Internal SDK Modules

The SDK includes internal modules for direct Solana access (installed with `pip install solanaeasy[solana]`):

### `_internal/solana/wallet.py`

| Function | Description |
|---|---|
| `generate_keypair()` | Create a new random Solana keypair |
| `keypair_from_secret(bytes)` | Reconstruct from secret key bytes |
| `keypair_from_base58(str)` | Reconstruct from base58 string |
| `public_key_str(keypair)` | Get the public key as a string |

### `_internal/solana/rpc.py`

| Function | Description |
|---|---|
| `get_sol_balance(pubkey, network)` | Get SOL balance for an address |
| `request_airdrop(pubkey, amount)` | Request devnet SOL (testing only) |
| `get_transaction_status(sig)` | Check if a transaction is confirmed |
| `transfer_sol(keypair, to, lamports)` | Transfer SOL between wallets |

!!! warning "Internal API"
    These modules are not part of the public SDK surface. They may change without notice. Use the `SolanaEasy` client for all integrations.

## Devnet Testing

The `drop.py` utility simulates customer payments during development:

```bash
.venv/bin/python drop.py <WALLET_ADDRESS>
```

**Behavior:**

1. Attempts a real Solana Devnet airdrop (1 SOL)
2. If the faucet is rate-limited, falls back to direct database injection
3. The backend's balance watcher detects the change and confirms the session
