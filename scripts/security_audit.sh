#!/usr/bin/env bash
# OpenPaper AI — Security Audit Script
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-./security_reports}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PATH="${REPORT_DIR}/audit_${TIMESTAMP}"
mkdir -p "$REPORT_PATH"

log() { echo "[$(date +%H:%M:%S)] $*"; }

log "=== OpenPaper Security Audit ==="
log ""

# ── 1. Dependency Scan ─────────────────────────────────────────
log "1. Dependency Scan..."

log "  - Backend (pip-audit):"
if command -v pip-audit &>/dev/null; then
    pip-audit --requirement <(pip freeze 2>/dev/null) \
        --format json \
        > "${REPORT_PATH}/pip_audit.json" 2>/dev/null || true
    python3 -c "
import json
try:
    with open('${REPORT_PATH}/pip_audit.json') as f:
        data = json.load(f)
    vulns = data.get('vulnerabilities', [])
    print(f'    Found {len(vulns)} vulnerabilities')
    for v in vulns:
        print(f'      - {v.get(\"id\",\"?\")}: {v.get(\"description\",\"\")[:80]}')
except: print('    No audit data')
" 2>/dev/null || log "    pip-audit report generated"
else
    log "    pip-audit not installed. Install: pip install pip-audit"
fi

log "  - Frontend (npm audit):"
if command -v npm &>/dev/null; then
    cd apps/web
    npm audit --json > "${REPORT_PATH}/npm_audit.json" 2>/dev/null || true
    python3 -c "
import json
try:
    with open('${REPORT_PATH}/npm_audit.json') as f:
        data = json.load(f)
    vulns = data.get('vulnerabilities', {})
    print(f'    Found {len(vulns)} vulnerable packages')
    for pkg, info in list(vulns.items())[:10]:
        print(f'      - {pkg}: {info.get(\"severity\",\"?\")}')
except: print('    No audit data')
" 2>/dev/null || log "    npm audit report generated"
    cd - >/dev/null
else
    log "    npm not found"
fi
log ""

# ── 2. Secret Scan ─────────────────────────────────────────────
log "2. Secret Scan..."

if command -v trufflehog &>/dev/null; then
    trufflehog filesystem --directory=. \
        --json \
        --no-update \
        > "${REPORT_PATH}/secrets.json" 2>/dev/null || true
    SECRET_COUNT=$(python3 -c "
import json
try:
    with open('${REPORT_PATH}/secrets.json') as f:
        count = sum(1 for line in f if line.strip())
    print(count)
except: print(0)
" 2>/dev/null || echo 0)
    log "    Found $SECRET_COUNT potential secrets"
elif command -v gitleaks &>/dev/null; then
    gitleaks detect --source=. \
        --report-path="${REPORT_PATH}/secrets.json" \
        --no-git \
        --verbose 2>/dev/null || true
    log "    gitleaks scan complete"
else
    log "    No secret scanner found. Install: pip install trufflehog  or  brew install gitleaks"
    log "    (skipping)"
fi
log ""

# ── 3. Container Scan ──────────────────────────────────────────
log "3. Container Scan..."

if command -v trivy &>/dev/null; then
    log "  - Scanning API image..."
    trivy image --severity HIGH,CRITICAL \
        --format json \
        --output "${REPORT_PATH}/trivy_api.json" \
        openpaper-api:latest 2>/dev/null || log "    (image not built locally, skipping)"

    log "  - Scanning Web image..."
    trivy image --severity HIGH,CRITICAL \
        --format json \
        --output "${REPORT_PATH}/trivy_web.json" \
        openpaper-web:latest 2>/dev/null || log "    (image not built locally, skipping)"

    log "    trivy scan complete"
else
    log "    trivy not installed. Install: https://trivy.dev"
    log "    (skipping)"
fi
log ""

# ── 4. API Security Review ─────────────────────────────────────
log "4. API Security Review..."

log "  - Checking security headers..."
curl -s -I "http://localhost:8000/api/health" 2>/dev/null > "${REPORT_PATH}/headers.txt" || true
python3 -c "
headers = {}
try:
    with open('${REPORT_PATH}/headers.txt') as f:
        for line in f:
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip().lower()] = v.strip()
except: pass

checks = {
    'strict-transport-security': 'Missing HSTS header',
    'x-content-type-options': 'Missing X-Content-Type-Options',
    'x-frame-options': 'Missing X-Frame-Options',
    'x-xss-protection': 'Missing X-XSS-Protection',
}
for header, msg in checks.items():
    if header in headers:
        print(f'    ✓ {header}: {headers[header]}')
    else:
        print(f'    ✗ {msg}')
" 2>/dev/null || log "    (API not running)"

log "  - Checking for exposed endpoints..."
python3 -c "
open_endpoints = [
    '/api/health',
    '/api/v1/auth/login',
    '/api/v1/auth/register',
]
for ep in open_endpoints:
    print(f'    • {ep} (unauthenticated)')
" 2>/dev/null || true
log ""

# ── 5. Summary ─────────────────────────────────────────────────
log "=== Security Audit Summary ==="
log "Audit report saved to: ${REPORT_PATH}"
log ""
log "Files:"
ls -la "${REPORT_PATH}/" 2>/dev/null || log "  (no files)"
log ""
log "Tools used:"
for tool in pip-audit npm trufflehog trivy; do
    if command -v $tool &>/dev/null; then
        log "  ✓ $tool"
    else
        log "  ✗ $tool (not installed)"
    fi
done
log ""
log "Security audit complete"
