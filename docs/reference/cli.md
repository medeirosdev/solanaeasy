# CLI Reference

The SDK installs a `solanaeasy` command for inspecting payments from the terminal.

## Installation

The CLI is installed automatically with the SDK:

```bash
pip install solanaeasy
```

## Configuration

The CLI reads your API key from the `SOLANAEASY_API_KEY` environment variable:

```bash
export SOLANAEASY_API_KEY=sk_test_1234567890
```

## Commands

### `solanaeasy status <session_id>`

Check the current status of a payment session.

```bash
$ solanaeasy status sess_abc123

Session: sess_abc123
State:   CONFIRMED
Message: Payment confirmed on the Solana Devnet.
Tx Hash: 5KtP9abc...
```

### `solanaeasy payments`

List recent payment sessions.

```bash
$ solanaeasy payments

 SESSION ID              STATE      AMOUNT  CURRENCY
 sess_abc123             CONFIRMED   50.00  USDC
 sess_def456             PENDING    150.00  USDC
 sess_ghi789             EXPIRED     25.00  USDC
```

**Options:**

| Flag | Description | Default |
|---|---|---|
| `--status STATE` | Filter by state | All |
| `--limit N` | Max results | 20 |
| `--offset N` | Pagination offset | 0 |

```bash
$ solanaeasy payments --status CONFIRMED --limit 5
```

### `solanaeasy wait <session_id>`

Poll a session until it reaches a terminal state. Shows real-time updates.

```bash
$ solanaeasy wait sess_abc123

Waiting for sess_abc123...
  → CREATED: Session created. Waiting for customer.
  → PENDING: Payment detected. Waiting for confirmation.
  → CONFIRMED: Payment confirmed on the Solana Devnet.

✓ Payment confirmed!
```

**Options:**

| Flag | Description | Default |
|---|---|---|
| `--timeout N` | Max seconds to wait | 120 |
| `--interval N` | Seconds between checks | 2 |

### `solanaeasy --version`

Print the SDK version.

```bash
$ solanaeasy --version
solanaeasy 0.1.0
```

### `solanaeasy --help`

Show all available commands and options.

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Error (invalid key, session not found, timeout, etc.) |
