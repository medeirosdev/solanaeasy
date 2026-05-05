# Installation

## Requirements

- Python **3.11** or higher
- An API key from the SolanaEasy dashboard

## Install from PyPI

```bash
pip install solanaeasy
```

## Optional: Solana Network Access

If you need direct access to the Solana blockchain (advanced use cases like custom RPC queries, wallet generation, or on-chain transfers):

```bash
pip install solanaeasy[solana]
```

This installs the additional `solders` and `solana` packages.

## Verify Installation

```python
import solanaeasy
print(solanaeasy.__version__)  # 0.1.0
```

## Environment Variables

The SDK reads configuration from environment variables when constructor arguments are omitted:

| Variable | Description | Default |
|---|---|---|
| `SOLANAEASY_API_KEY` | Your API key | *(required)* |
| `SOLANAEASY_NETWORK` | `devnet` or `mainnet-beta` | `devnet` |
| `SOLANAEASY_BASE_URL` | Backend URL | `http://localhost:8000` (devnet) |
| `SOLANAEASY_WEBHOOK_SECRET` | Webhook signing secret | *(optional)* |
| `SOLANAEASY_TIMEOUT` | HTTP timeout in seconds | `30` |

You can use a `.env` file — the SDK loads it automatically via `python-dotenv`.

```bash title=".env"
SOLANAEASY_API_KEY=sk_test_1234567890
SOLANAEASY_NETWORK=devnet
SOLANAEASY_BASE_URL=http://localhost:8000
```

## Next Steps

[:material-arrow-right: Quickstart Guide](quickstart.md){ .md-button .md-button--primary }
