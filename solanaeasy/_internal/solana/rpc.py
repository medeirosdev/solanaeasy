"""
SolanaEasy — Internal Solana RPC client.

Handles direct communication with the Solana network:
- Balance checks (SOL and SPL tokens)
- Devnet airdrops (testing only)
- Transaction status monitoring
- USDC transfer building

Requires: pip install solanaeasy[solana]
"""

from __future__ import annotations

import time
from typing import Any

try:
    from solana.rpc.api import Client                    # type: ignore[import]
    from solana.rpc.types import TxOpts                  # type: ignore[import]
    from solders.pubkey import Pubkey                    # type: ignore[import]
    from solders.signature import Signature              # type: ignore[import]
    from solders.system_program import TransferParams, transfer  # type: ignore[import]
    from solders.transaction import Transaction          # type: ignore[import]
    from solders.message import Message                  # type: ignore[import]
    from solders.keypair import Keypair                  # type: ignore[import]
    _SOLANA_AVAILABLE = True
except ImportError:
    _SOLANA_AVAILABLE = False

# RPC endpoints
DEVNET_RPC_URL = "https://api.devnet.solana.com"
MAINNET_RPC_URL = "https://api.mainnet-beta.solana.com"

# USDC mint addresses
USDC_DEVNET_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
USDC_MAINNET_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Solana constants
LAMPORTS_PER_SOL = 1_000_000_000


def _require_solana() -> None:
    if not _SOLANA_AVAILABLE:
        raise ImportError(
            "Direct Solana RPC requires optional dependencies. "
            "Install with: pip install solanaeasy[solana]"
        )


def get_rpc_client(network: str = "devnet") -> "Client":
    """Return a connected Solana RPC client for the given network."""
    _require_solana()
    url = DEVNET_RPC_URL if network == "devnet" else MAINNET_RPC_URL
    return Client(url)


def get_sol_balance(public_key: str, network: str = "devnet") -> float:
    """
    Get SOL balance for a wallet address.

    Parameters:
        public_key: Base58 wallet address.
        network:    "devnet" or "mainnet-beta".

    Returns:
        Balance in SOL (float). 1 SOL = 1_000_000_000 lamports.
    """
    _require_solana()
    client = get_rpc_client(network)
    response = client.get_balance(Pubkey.from_string(public_key))
    lamports = response.value
    return lamports / LAMPORTS_PER_SOL


def request_airdrop(
    public_key: str,
    sol_amount: float = 1.0,
    network: str = "devnet",
    wait_for_confirmation: bool = True,
) -> str:
    """
    Request a SOL airdrop on devnet (free test tokens).

    Only works on devnet — will raise on mainnet.
    Limited to ~2 SOL per request by the devnet faucet.

    Parameters:
        public_key:            Wallet address to receive SOL.
        sol_amount:            Amount in SOL (default: 1.0).
        network:               Must be "devnet".
        wait_for_confirmation: If True, waits up to 30s for on-chain confirmation.

    Returns:
        Transaction signature (base58 string).

    Raises:
        ValueError: If called on mainnet.
    """
    _require_solana()
    if network != "devnet":
        raise ValueError("Airdrops are only available on devnet.")

    client = get_rpc_client(network)
    lamports = int(sol_amount * LAMPORTS_PER_SOL)
    response = client.request_airdrop(Pubkey.from_string(public_key), lamports)
    signature = str(response.value)

    if wait_for_confirmation:
        _wait_for_tx(client, signature, timeout=30)

    return signature


def get_transaction_status(tx_signature: str, network: str = "devnet") -> dict[str, Any]:
    """
    Get the status of a transaction by its signature.

    Parameters:
        tx_signature: Base58 transaction signature.
        network:      "devnet" or "mainnet-beta".

    Returns:
        Dict with keys:
        - confirmed (bool): True if finalized
        - slot (int | None): Block slot
        - error (str | None): Error message if failed
    """
    _require_solana()
    client = get_rpc_client(network)
    response = client.get_transaction(
        Signature.from_string(tx_signature),
        max_supported_transaction_version=0,
    )

    if response.value is None:
        return {"confirmed": False, "slot": None, "error": None}

    tx = response.value
    error = None
    if tx.transaction.meta and tx.transaction.meta.err:
        error = str(tx.transaction.meta.err)

    return {
        "confirmed": True,
        "slot": tx.slot,
        "error": error,
    }


def transfer_sol(
    from_keypair: "Keypair",
    to_public_key: str,
    lamports: int,
    network: str = "devnet",
) -> str:
    """
    Transfer SOL from one wallet to another.

    Parameters:
        from_keypair:  Keypair of the sender (signs the transaction).
        to_public_key: Recipient's base58 wallet address.
        lamports:      Amount in lamports (1 SOL = 1_000_000_000 lamports).
        network:       "devnet" or "mainnet-beta".

    Returns:
        Transaction signature (base58 string).
    """
    _require_solana()
    client = get_rpc_client(network)

    blockhash_response = client.get_latest_blockhash()
    recent_blockhash = blockhash_response.value.blockhash

    transfer_ix = transfer(
        TransferParams(
            from_pubkey=from_keypair.pubkey(),
            to_pubkey=Pubkey.from_string(to_public_key),
            lamports=lamports,
        )
    )

    msg = Message.new_with_blockhash(
        [transfer_ix],
        from_keypair.pubkey(),
        recent_blockhash,
    )
    tx = Transaction([from_keypair], msg, recent_blockhash)

    response = client.send_transaction(
        tx,
        opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed"),
    )
    return str(response.value)


def _wait_for_tx(client: "Client", signature: str, timeout: int = 30) -> bool:
    """
    Wait for a transaction to be confirmed on-chain.

    Returns True if confirmed within timeout, False otherwise.
    """
    _require_solana()
    deadline = time.monotonic() + timeout
    sig = Signature.from_string(signature)

    while time.monotonic() < deadline:
        response = client.get_signature_statuses([sig])
        status = response.value[0]
        if status is not None and status.confirmation_status is not None:
            return True
        time.sleep(1)

    return False
