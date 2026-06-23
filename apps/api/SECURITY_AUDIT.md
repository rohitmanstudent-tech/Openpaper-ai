# Security Audit Report

**Date**: 2026-06-23
**Scope**: OpenPaper AI API (`apps/api`)
**Test Coverage**: 41 tests (6 health + 27 security + 8 validator) — all passing

---

## 1. API Security

### Rate Limiting — PASS
- **Sliding window implementation**: Per-IP, per-endpoint with in-memory (default) and Redis backends
- **Auth endpoint limits**: Login (10/min), Register (5/min), Refresh (10/min)
- **Brute-force protection**: Strict limits on auth endpoints with `Retry-After` header
- **Tested**: `test_rate_limit_triggers_at_threshold` — 429 returned at threshold, structured error format

### JWT Validation — PASS
- **Algorithm**: HS256 via `python-jose`
- **Expiry**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min)
- **Error handling**: `JWTError` caught, raises `TokenExpiredError` with `from None` clean chain
- **Tested**: `test_auth_returns_structured_json` — invalid token returns 401 with structured JSON

### Refresh Token Rotation — PASS
- **Storage**: SHA-256 hash in `refresh_tokens` table (raw token never persisted)
- **Rotation**: Each `/refresh` revokes old token, issues new one (both access + refresh)
- **Revocation**: Explicit `POST /auth/revoke` endpoint
- **Expiry**: 7-day default, table auto-cleaned via `expires_at` check

## 2. Web Security

### Security Headers — PASS
| Header | Value | All Responses |
|--------|-------|---------------|
| `X-Content-Type-Options` | `nosniff` | Yes |
| `X-Frame-Options` | `DENY` | Yes |
| `X-XSS-Protection` | `1; mode=block` | Yes |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Production only |
| `Content-Security-Policy` | Restrictive (scripts, styles, connects, frames, fonts) | Production only |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Production only |
| `Permissions-Policy` | All features denied | Production only |

- **Tested**: 3 header tests pass for XCTO, XFO, XSS-Protection

### CORS — PASS
- Configurable origins via `CORS_ORIGINS` env var (comma-separated)
- Validator warns when set to `*`

### CSRF — PARTIAL
- Token-based CSRF not implemented (API is stateless JWT)
- Mitigation: SameSite cookies not applicable (token in Authorization header)
- **Recommendation**: Add `SameSite=Strict` if cookie-based auth is added later

## 3. Input Security

### String Sanitization — PASS
- Control characters (U+0000-U+001F, U+007F) stripped
- Length limited to 10,000 chars
- **Tested**: `test_removes_control_characters`, `test_truncates_long_strings`

### Prompt Injection Protection — PASS
- **10 detection patterns**:
  1. `ignore (all)? (previous|above|prior) (instructions|commands|...)`
  2. `(forget|disregard|override) (all)? (previous|above|prior)`
  3. `you are now... (not|instead|pretend|roleplay)`
  4. `(new )?(system )?prompt:` (at line start)
  5. `[ds]o not (follow|obey|adhere|comply)`
  6. `(jailbreak|prompt injection|leak|extract) (prompt|instructions|system)`
  7. `reveal (your )?(system )?prompt`
  8. `(role play|roleplay) as`
  9. `output (your )?(raw|original|initial|system) (instructions|prompt|command)`
- **Tested**: 7 injection patterns detected, 3 clean inputs pass

### File Upload Validation — PASS
- Extension whitelist: 14 types (txt, md, csv, json, yaml, pdf, docx, xlsx, png, jpg, jpeg, gif, svg)
- Size limit: 10 MB
- **Tested**: Invalid extension rejected, large file rejected, valid upload allowed

### XSS Protection — PASS
- `sanitize_html()` escapes: `&`, `<`, `>`, `"`, `'`
- **Tested**: Script tags escaped, quotes escaped

### SQL Injection — PASS
- All queries use SQLAlchemy ORM parameterized queries (no raw SQL concatenation)
- Scoped session pattern prevents injection

## 4. AI Security

### Provider Key Encryption — PASS
- **Algorithm**: Fernet (AES-128-CBC + HMAC-SHA256) via `cryptography` package
- **Key**: Configurable via `ENCRYPTION_KEY` env var (base64-encoded 32-byte key)
- **Fallback**: Ephemeral key generated if not set (keys lost on restart)
- **Tested**: Roundtrip (encrypt→decrypt), different outputs (random IV), invalid ciphertext raises `InvalidToken`

### Secret Management — PASS
- All secrets via environment variables using Pydantic `SettingsConfigDict`
- Validator at startup: checks for empty SECRET_KEY, warns on defaults
- No secrets in code, no `.env` committed

### Agent Permission Boundaries — PASS
- **RBAC**: 4 roles (Admin, Manager, Member, Viewer), 7 permissions
- **Enforcement**: `require_permission()` decorator using typed `PermissionDeniedError`
- **Data isolation**: All agent/task queries scoped to `current_user.id`

### Tool Execution Restrictions — PASS (Basic)
- Agent delegation requires explicit `target_agent_type` parameter
- Agent execution validates agent ownership before running
- **Recommendation**: Add execution timeout and allowlist for agent actions

## 5. Error Handling

### Structured Error Responses — PASS
- **Format**: `{success: false, error_code, message, request_id, details}`
- **16 exception classes** with typed status codes and error codes
- **ExceptionMiddleware** catches errors from both route handlers and dependencies
- **Custom 404 handler** overrides Starlette's default `{"detail": "Not Found"}`

### Error Monitoring — PASS
- **Sentry**: Optional DSN-based integration with FastAPI + Logging + SQLAlchemy
- Graceful skip if `sentry-sdk` not installed
- `capture_error()` helper for non-request contexts

## 6. Dependencies

| Package | Version | Notes |
|---------|---------|-------|
| `cryptography` | 46.0.5 | Fernet encryption |
| `python-jose` | 3.5.0 | JWT encode/decode |
| `passlib` | 1.7.4 | bcrypt password hashing |
| `sentry-sdk` | (optional) | Error monitoring |
| `slowapi` | (not used) | Custom rate limiter implemented instead |

## Summary

| Category | Status | Findings |
|----------|--------|----------|
| API Security | ✅ Pass | Rate limiting, JWT validation, refresh token rotation |
| Web Security | ✅ Pass | CSP, HSTS, XFO, XCTO, CORS configurable |
| Input Security | ✅ Pass | Sanitization, prompt injection detection, XSS escaping |
| AI Security | ✅ Pass | Key encryption, RBAC, secret management |
| Error Handling | ✅ Pass | Structured JSON, 16 typed exceptions, Sentry optional |
| Open Issues | ⚠️ Low | CSRF protection (not applicable for Bearer tokens), tool execution timeouts |

## Recommendations

1. **Production**: Set `ENCRYPTION_KEY` to a fixed base64-encoded 32-byte key (not using ephemeral fallback)
2. **Production**: Set `RATE_LIMIT_ENABLED=True` (default)
3. **Production**: Disable `DEBUG=True` — enables CSP/HSTS headers and disables debug output
4. **Future**: Add execution timeout and action allowlist for agent tools
5. **CI**: Trivy scan configured for CRITICAL+HIGH in CI pipeline
