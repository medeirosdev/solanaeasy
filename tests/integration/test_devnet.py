"""
Integration tests against the Solana DEVNET.

These tests make real network calls and require:
    pip install solanaeasy[solana]

Run with:
    pytest tests/integration/ -v -m integration

They are excluded from the default test run (unit tests only).
No real money is used — devnet SOL has no value.

What is tested:
    1. Wallet generation (keypair creation)
    2. Devnet airdrop (free SOL from the faucet)
    3. SOL balance verification
    4. SOL transfer between two wallets
    5. Transaction status confirmation
"""

from __future__ import annotations

import time

import pytest

# These tests require the optional [solana] extras
solana_available = True
try:
    from solanaeasy._internal.solana.wallet import (
        generate_keypair,
        public_key_str,
        keypair_to_dict,
    )
    from solanaeasy._internal.solana.rpc import (
        get_sol_balance,
        request_airdrop,
        transfer_sol,
        get_transaction_status,
        LAMPORTS_PER_SOL,
    )
except ImportError:
    solana_available = False

pytestmark = pytest.mark.integration

requires_solana = pytest.mark.skipif(
    not solana_available,
    reason="Requires: pip install solanaeasy[solana]",
)


# ── Test 1: Wallet generation (no network needed) ─────────────────────────────

@requires_solana
def test_generate_keypair():
    """Each call generates a unique keypair."""
    kp1 = generate_keypair()
    kp2 = generate_keypair()

    assert public_key_str(kp1) != public_key_str(kp2)
    assert len(public_key_str(kp1)) == 44  # base58 public key length


@requires_solana
def test_keypair_serialization():
    """Keypair can be serialized and is deterministic."""
    kp = generate_keypair()
    d = keypair_to_dict(kp)

    assert "public_key" in d
    assert "secret_key" in d
    assert len(d["secret_key"]) == 64   # 64 bytes: 32 private + 32 public
    assert d["public_key"] == public_key_str(kp)


# ── Test 2: Devnet airdrop ─────────────────────────────────────────────────────

@requires_solana
def test_devnet_airdrop():
    """
    Request 0.5 SOL from the devnet faucet and verify it arrives.

    Network: devnet | Real money: NO
    Expected time: ~5-15 seconds for on-chain confirmation.
    """
    kp = generate_keypair()
    pubkey = public_key_str(kp)

    # Verify initial balance is 0
    initial_balance = get_sol_balance(pubkey, network="devnet")
    assert initial_balance == 0.0

    # Request airdrop (waits for confirmation internally)
    sig = request_airdrop(pubkey, sol_amount=0.5, network="devnet", wait_for_confirmation=True)

    assert sig is not None
    assert len(sig) > 40  # valid base58 signature

    # Verify funds arrived
    balance = get_sol_balance(pubkey, network="devnet")
    assert balance == pytest.approx(0.5, abs=0.001)

    print(f"\n✅ Airdrop confirmed!")
    print(f"   Wallet:  {pubkey}")
    print(f"   Balance: {balance:.4f} SOL")
    print(f"   TX sig:  {sig}")


# ── Test 3: SOL transfer ──────────────────────────────────────────────────────

@requires_solana
def test_sol_transfer_between_wallets():
    """
    Fund wallet A via airdrop, then transfer SOL to wallet B.

    Network: devnet | Real money: NO
    Expected time: ~15-30 seconds.
    """
    sender = generate_keypair()
    receiver = generate_keypair()

    sender_pubkey = public_key_str(sender)
    receiver_pubkey = public_key_str(receiver)

    # Fund the sender
    print(f"\n⏳ Requesting airdrop for sender: {sender_pubkey[:8]}...")
    request_airdrop(sender_pubkey, sol_amount=1.0, network="devnet", wait_for_confirmation=True)

    sender_balance_before = get_sol_balance(sender_pubkey, network="devnet")
    assert sender_balance_before > 0

    # Transfer 0.1 SOL (100_000_000 lamports)
    transfer_amount_lamports = int(0.1 * LAMPORTS_PER_SOL)

    print(f"⏳ Transferring 0.1 SOL to receiver: {receiver_pubkey[:8]}...")
    tx_sig = transfer_sol(
        from_keypair=sender,
        to_public_key=receiver_pubkey,
        lamports=transfer_amount_lamports,
        network="devnet",
    )

    # Wait for the transfer to be confirmed
    time.sleep(5)

    receiver_balance = get_sol_balance(receiver_pubkey, network="devnet")
    assert receiver_balance == pytest.approx(0.1, abs=0.001)

    # Verify the transaction status
    tx_status = get_transaction_status(tx_sig, network="devnet")
    assert tx_status["confirmed"] is True
    assert tx_status["error"] is None

    print(f"✅ Transfer confirmed!")
    print(f"   Sender:   {sender_pubkey[:8]}...  → {get_sol_balance(sender_pubkey, 'devnet'):.4f} SOL")
    print(f"   Receiver: {receiver_pubkey[:8]}...  → {receiver_balance:.4f} SOL")
    print(f"   TX sig:   {tx_sig}")


# ── Test 4: Transaction status ────────────────────────────────────────────────

@requires_solana
def test_transaction_status_after_airdrop():
    """Verify that get_transaction_status returns correct info after airdrop."""
    kp = generate_keypair()
    pubkey = public_key_str(kp)

    sig = request_airdrop(pubkey, sol_amount=0.1, network="devnet", wait_for_confirmation=True)
    time.sleep(2)

    status = get_transaction_status(sig, network="devnet")

    assert status["confirmed"] is True
    assert status["error"] is None
    assert status["slot"] is not None
    assert status["slot"] > 0
