"""
Wallet signature verification for Radius.

Verifies that a user controls a wallet by checking a signed message.
The message format is: "radius-verify:{entity_id}:{date}"

This proves wallet ownership without requiring any on-chain transaction.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from eth_account import Account
from eth_account.messages import encode_defunct


@dataclass
class VerificationResult:
    """Result of a wallet verification attempt."""
    is_valid: bool
    recovered_address: Optional[str] = None
    error: Optional[str] = None


def verify_wallet_signature(
    wallet: str,
    message: str,
    signature: str,
) -> VerificationResult:
    """
    Verify that a signature was created by the owner of the given wallet.

    Args:
        wallet: The Ethereum address claiming ownership (0x...)
        message: The message that was signed
        signature: The signature (0x...)

    Returns:
        VerificationResult with is_valid=True if signature matches wallet
    """
    try:
        # Simpler approach: just lowercase compare
        wallet_lower = wallet.lower()

        # Encode the message for Ethereum signed message format
        # This adds the "\x19Ethereum Signed Message:\n" prefix
        message_encoded = encode_defunct(text=message)

        # Recover the address that signed this message
        recovered_address = Account.recover_message(message_encoded, signature=signature)

        # Compare addresses (case-insensitive)
        if recovered_address.lower() == wallet_lower:
            return VerificationResult(
                is_valid=True,
                recovered_address=recovered_address,
            )
        else:
            return VerificationResult(
                is_valid=False,
                recovered_address=recovered_address,
                error=f"Signature is from {recovered_address}, not {wallet}",
            )

    except Exception as e:
        return VerificationResult(
            is_valid=False,
            error=f"Signature verification failed: {str(e)}",
        )


def generate_verification_message(entity_id: str, date: Optional[str] = None) -> str:
    """
    Generate the message that should be signed for wallet verification.

    Args:
        entity_id: The entity ID to bind the wallet to
        date: Optional date string (YYYY-MM-DD). Defaults to today.

    Returns:
        The message string to be signed
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    return f"radius-verify:{entity_id}:{date}"


def is_message_expired(message: str, max_age_days: int = 7) -> bool:
    """
    Check if a verification message has expired.

    Args:
        message: The signed message
        max_age_days: Maximum age in days (default 7)

    Returns:
        True if message is expired
    """
    try:
        # Extract date from message format "radius-verify:{entity_id}:{date}"
        parts = message.split(":")
        if len(parts) != 3 or parts[0] != "radius-verify":
            return True  # Invalid format = expired

        date_str = parts[2]
        message_date = datetime.strptime(date_str, "%Y-%m-%d")
        expiry = message_date + timedelta(days=max_age_days)

        return datetime.utcnow() > expiry

    except (ValueError, IndexError):
        return True  # Can't parse = treat as expired
