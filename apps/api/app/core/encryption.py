"""Provider API key encryption using Fernet symmetric encryption."""

import base64
import logging

from cryptography.fernet import Fernet

from app.config import get_settings

logger = logging.getLogger(__name__)

_cipher: Fernet | None = None


def _get_or_create_key() -> str:
    settings = get_settings()
    raw = settings.ENCRYPTION_KEY
    if not raw:
        raise RuntimeError("ENCRYPTION_KEY must be set in production")
    try:
        base64.urlsafe_b64decode(raw)
    except Exception:
        raise RuntimeError("ENCRYPTION_KEY is not valid base64") from None
    return raw


def init_encryption() -> None:
    global _cipher
    key = _get_or_create_key()
    _cipher = Fernet(key)


def encrypt_value(plaintext: str) -> str:
    if _cipher is None:
        init_encryption()
    return _cipher.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    if _cipher is None:
        init_encryption()
    return _cipher.decrypt(ciphertext.encode()).decode()
