"""
SolanaEasy — Internal wallet/keypair management.

Handles generation and management of temporary Solana keypairs per payment session.
Requires: pip install solanaeasy[solana]
"""

from __future__ import annotations

try:
    from solders.keypair import Keypair  # type: ignore[import]
    from solders.pubkey import Pubkey    # type: ignore[import]
    _SOLANA_AVAILABLE = True
except ImportError:
    _SOLANA_AVAILABLE = False


def _require_solana() -> None:
    if not _SOLANA_AVAILABLE:
        raise ImportError(
            "Direct Solana access requires optional dependencies. "
            "Install with: pip install solanaeasy[solana]"
        )


def generate_keypair() -> "Keypair":
    """
    Generate a new random Solana keypair.

    Used internally to create temporary wallets per payment session.
    Each session gets its own keypair so funds are isolated.

    Returns:
        A new Keypair with a random private key.
    """
    _require_solana()
    return Keypair()


def keypair_from_secret(secret_bytes: bytes) -> "Keypair":
    """
    Reconstruct a keypair from its secret key bytes.

    Parameters:
        secret_bytes: 64-byte secret key (private + public).

    Returns:
        The corresponding Keypair.
    """
    _require_solana()
    return Keypair.from_bytes(secret_bytes)


def keypair_from_base58(secret_base58: str) -> "Keypair":
    """
    Reconstruct a keypair from a base58-encoded secret key string.
    Useful for loading wallets from environment variables.

    Parameters:
        secret_base58: Base58-encoded secret key string.

    Returns:
        The corresponding Keypair.
    """
    _require_solana()
    import base58  # type: ignore[import]
    return Keypair.from_bytes(base58.b58decode(secret_base58))


def public_key_str(keypair: "Keypair") -> str:
    """Return the public key as a base58 string (wallet address)."""
    _require_solana()
    return str(keypair.pubkey())


def keypair_to_dict(keypair: "Keypair") -> dict[str, object]:
    """
    Serialize a keypair to a JSON-safe dict.
    WARNING: contains the private key — never log or expose this.

    Returns:
        {
            "public_key": "base58 address",
            "secret_key": [byte, byte, ...]   ← 64 bytes
        }
    """
    _require_solana()
    return {
        "public_key": str(keypair.pubkey()),
        "secret_key": list(bytes(keypair)),
    }
