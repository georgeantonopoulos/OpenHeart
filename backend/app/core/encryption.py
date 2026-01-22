"""
PII Encryption for OpenHeart Cyprus.

Provides Fernet-based encryption for Personally Identifiable Information
as required by GDPR and Cyprus Law 125(I)/2018.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """
    Get Fernet instance with the configured encryption key.

    The key is derived from the configured PII_ENCRYPTION_KEY setting.
    If the key is not a valid Fernet key, it's derived using SHA-256.

    Returns:
        Fernet instance for encryption/decryption
    """
    key = settings.pii_encryption_key

    # Check if key is already a valid Fernet key (base64-encoded 32 bytes)
    try:
        # Valid Fernet key is 32 url-safe base64-encoded bytes
        decoded = base64.urlsafe_b64decode(key)
        if len(decoded) == 32:
            return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        pass

    # Derive a valid key from the provided key using SHA-256
    derived_key = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived_key)
    return Fernet(fernet_key)


def encrypt_pii(plaintext: str) -> str:
    """
    Encrypt PII data using Fernet symmetric encryption.

    Args:
        plaintext: Plain text PII to encrypt

    Returns:
        Base64-encoded encrypted string

    Example:
        >>> encrypted = encrypt_pii("CY12345678")
        >>> decrypted = decrypt_pii(encrypted)
        >>> assert decrypted == "CY12345678"
    """
    if not plaintext:
        return ""

    fernet = _get_fernet()
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_pii(ciphertext: str) -> str:
    """
    Decrypt PII data.

    Args:
        ciphertext: Encrypted PII string

    Returns:
        Decrypted plain text

    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    if not ciphertext:
        return ""

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken as e:
        logger.error(f"Failed to decrypt PII: Invalid token - {e}")
        raise ValueError("Failed to decrypt PII: invalid encryption key or corrupted data")
    except Exception as e:
        logger.error(f"Failed to decrypt PII: {e}")
        raise ValueError(f"Failed to decrypt PII: {e}")


def encrypt_pii_optional(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypt PII data, handling None values.

    Args:
        plaintext: Plain text PII to encrypt, or None

    Returns:
        Encrypted string or None
    """
    if plaintext is None:
        return None
    return encrypt_pii(plaintext)


def decrypt_pii_optional(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypt PII data, handling None values.

    Args:
        ciphertext: Encrypted PII string, or None

    Returns:
        Decrypted string or None
    """
    if ciphertext is None:
        return None
    return decrypt_pii(ciphertext)


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Use this to generate a new PII_ENCRYPTION_KEY for production.

    Returns:
        Base64-encoded Fernet key
    """
    return Fernet.generate_key().decode("utf-8")


def mask_pii(value: str, visible_chars: int = 4) -> str:
    """
    Mask PII for display purposes.

    Shows only the last few characters, replacing the rest with asterisks.

    Args:
        value: PII value to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked string (e.g., "****5678")

    Example:
        >>> mask_pii("CY12345678")
        '******5678'
    """
    if not value or len(value) <= visible_chars:
        return "*" * len(value) if value else ""

    masked_length = len(value) - visible_chars
    return "*" * masked_length + value[-visible_chars:]


def hash_identifier(identifier: str) -> str:
    """
    Create a one-way hash of an identifier for indexing.

    This allows searching encrypted fields without decrypting.

    Args:
        identifier: Identifier to hash (e.g., Cyprus ID)

    Returns:
        SHA-256 hash of the identifier
    """
    return hashlib.sha256(
        (identifier + settings.secret_key).encode()
    ).hexdigest()
