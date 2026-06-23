# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.0.x (release candidates) | ✅ Security patches |
| 0.x (sprint releases) | ❌ End of life |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in OpenPaper AI, please **do not** open a public issue.

Instead, send a detailed report to **[security@openpaper.ai](mailto:security@openpaper.ai)**.

### What to include

- Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
- Steps to reproduce with minimum required configuration
- Proof of concept code (if applicable)
- Impact assessment
- Suggested fix (optional but appreciated)

### Response SLA

| Timeframe | Action |
|---|---|
| 48 hours | Acknowledgment of receipt |
| 7 days | Initial assessment and triage |
| 30 days | Fix or mitigation deployed for supported versions |

### What to expect

1. We will acknowledge receipt within 48 hours
2. We will assess and triage within 7 days
3. We will work on a fix and keep you informed of progress
4. We will credit you in the release notes (if desired)

## Security Measures

### Authentication & Authorization

| Measure | Implementation |
|---|---|
| JWT tokens | HS256-signed, configurable expiry (default 30 min) |
| Refresh tokens | SHA-256 hashed in DB, rotation on each use, 7-day TTL |
| Password hashing | bcrypt via passlib |
| RBAC | 4 roles (admin, user, viewer, api) with 7 permissions |
| Rate limiting | Sliding window, per-endpoint config, Redis-backed |

### API Security

| Measure | Implementation |
|---|---|
| CSP | Production-only Content-Security-Policy header |
| HSTS | Strict-Transport-Security: max-age=31536000 |
| X-Frame-Options | DENY on all responses |
| X-Content-Type-Options | nosniff on all responses |
| CORS | Configurable origins via CORS_ORIGINS env var |

### Data Security

| Measure | Implementation |
|---|---|
| Provider keys | Fernet symmetric encryption (AES-128-CBC) |
| DB secrets | Environment variables only (Pydantic settings) |
| SQL injection | Prevented by SQLAlchemy ORM parameterized queries |
| Input sanitization | Control char stripping, length limiting |
| XSS prevention | HTML special character escaping |

### AI Security

| Measure | Implementation |
|---|---|
| Prompt injection | 10 regex patterns detecting jailbreak attempts |
| Agent permissions | Sandboxed via PluginRegistry with permission enforcement |
| File uploads | 14-type extension whitelist, 10 MB limit |

### Infrastructure Security

| Measure | Implementation |
|---|---|
| Container security | Non-root user (openpaper) in Docker images |
| Dependency scanning | pip-audit + npm audit in CI |
| Secret scanning | trufflehog/gitleaks in CI |
| Container scanning | Trivy vulnerability scanner in CI |

## Security Audit

The CI pipeline runs automated security checks on every push:

```bash
# Manual audit
./scripts/security_audit.sh
```

This runs:
1. pip-audit — Python dependency vulnerability scan
2. npm audit — JavaScript dependency vulnerability scan
3. trufflehog/gitleaks — Secret leakage scan on git history
4. trivy — Container image vulnerability scan
5. API header review — Security headers presence check

## Responsible Disclosure

We follow a 90-day disclosure deadline. After a fix is released, we encourage researchers to publish their findings. We will coordinate disclosure to protect users.

## Known Security Considerations

- **Local development:** Default secrets (`SECRET_KEY`, `ENCRYPTION_KEY`) in `.env.example` must be changed for production
- **Ollama:** Local Ollama instances should be bound to `127.0.0.1` in production
- **Qdrant:** Qdrant API key should be configured for production deployments
- **HTTPS:** Traefik SSL termination required for production; HSTS assumes HTTPS

## Third-Party Security

- [FastAPI Security](https://fastapi.tiangolo.com/features/#security)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/core/engines.html#sql-injection)
- [JWT Best Practices](https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/)
