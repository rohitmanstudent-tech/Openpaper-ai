"""OpenPaper Hub — signature verification and trust system.

Supports Ed25519 signing of package manifests,
signature verification on install, and publisher key management."""

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


try:
    from nacl.encoding import HexEncoder
    from nacl.signing import SigningKey, VerifyKey

    _HAS_NACL = True
except ImportError:
    SigningKey = None
    VerifyKey = None
    HexEncoder = None
    _HAS_NACL = False
    logger.warning("PyNaCl not installed — signature verification disabled. Install with: pip install pynacl")


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_checksum(manifest: dict[str, Any]) -> str:
    canonical = _canonical_json(manifest)
    return _sha256(canonical)


def _canonical_json(obj: Any) -> str:
    import json
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def generate_key_pair() -> dict[str, str]:
    if not _HAS_NACL:
        raise RuntimeError(
            "PyNaCl is required for key generation. "
            "Install with: pip install pynacl"
        )
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    return {
        "private_key": signing_key.encode(encoder=HexEncoder).decode(),
        "public_key": verify_key.encode(encoder=HexEncoder).decode(),
        "key_id": _sha256(verify_key.encode(encoder=HexEncoder).decode())[:16],
    }


def sign_manifest(manifest: dict[str, Any], private_key_hex: str) -> str:
    if not _HAS_NACL:
        raise RuntimeError(
            "PyNaCl is required for signing. "
            "Install with: pip install pynacl"
        )
    signing_key = SigningKey(private_key_hex, encoder=HexEncoder)
    canonical = _canonical_json(manifest)
    signed = signing_key.sign(canonical.encode("utf-8"), encoder=HexEncoder)
    return signed.signature.decode()


def verify_signature(
    manifest: dict[str, Any],
    signature_hex: str,
    public_key_hex: str,
) -> bool:
    if not _HAS_NACL:
        logger.warning("PyNaCl not available — skipping signature verification")
        return True
    try:
        verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)
        canonical = _canonical_json(manifest)
        verify_key.verify(canonical.encode("utf-8"), bytes.fromhex(signature_hex))
        return True
    except Exception as e:
        logger.warning("Signature verification failed: %s", e)
        return False


def compute_package_hash(source_archive: str | bytes) -> str:
    if isinstance(source_archive, str):
        source_archive = source_archive.encode("utf-8")
    return _sha256(source_archive)
