"""CLI-side signature creation for package publishing.

Mirrors the backend signer but only exposes signing (not verification)
since the CLI signs before uploading to the registry."""

import hashlib
import json
from typing import Any


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


try:
    from nacl.signing import SigningKey
    from nacl.encoding import HexEncoder

    _HAS_NACL = True
except ImportError:
    SigningKey = None
    HexEncoder = None
    _HAS_NACL = False


def sign_manifest(manifest: dict[str, Any], private_key_hex: str) -> str:
    if not _HAS_NACL:
        raise RuntimeError(
            "PyNaCl is required for signing. Install with: pip install pynacl"
        )
    signing_key = SigningKey(private_key_hex, encoder=HexEncoder)
    canonical = _canonical_json(manifest)
    signed = signing_key.sign(canonical.encode("utf-8"), encoder=HexEncoder)
    return signed.signature.decode()
