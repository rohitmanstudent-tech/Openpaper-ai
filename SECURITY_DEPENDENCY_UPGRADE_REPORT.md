# Security Dependency Upgrade Report

## Summary
Upgraded two Python packages in `apps/api/pyproject.toml` to resolve CRITICAL/HIGH vulnerabilities detected by Trivy.

| Package | Old Min | New Min | Installed |
|---------|---------|---------|-----------|
| `python-jose[cryptography]` | `>=3.4.0` | `>=3.5.0` | 3.5.0 |
| `python-multipart` | `>=0.0.30` | `>=0.0.32` | 0.0.32 |

## python-jose 3.4.0 → 3.5.0
- **Released:** 2025-05-28
- **Security fixes:** Upgrades `pyasn1` to 0.5.1+ (addresses dependency CVEs), removes EOL Python 3.8 support, adds Python 3.12/3.13 support
- **API compatibility:** No breaking changes — `jwt.encode()`, `jwt.decode()`, `JWTError` signatures unchanged
- **Usage in project:** `app/core/security.py` — JWT token creation and validation via `jose.jwt`

## python-multipart 0.0.30 → 0.0.32
- **Released:** 2026-06-04
- **Security fixes:** Multiple vulnerability patches across 0.0.31 and 0.0.32
- **API compatibility:** Fully backward compatible — used implicitly by FastAPI `UploadFile`/`File()`, no direct imports in project code

## Verification
- Tests: **308 passed, 9 skipped, 0 failed**
- Ruff: 0 violations
- No breaking changes detected in either upgrade
