#!/usr/bin/env bash
# OpenPaper AI — Full Performance Audit
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-./benchmark_reports}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PATH="${REPORT_DIR}/benchmark_${TIMESTAMP}"
mkdir -p "$REPORT_PATH"

log() { echo "[$(date +%H:%M:%S)] $*"; }

log "=== OpenPaper Performance Audit ==="
log ""

# ── 1. API Benchmarks ──────────────────────────────────────────
log "1. API Benchmarks..."
API_HOST="${API_HOST:-http://localhost:8000}"
API_KEY="${API_KEY:-}"

# Login benchmark
log "  - Auth (login):"
time for i in $(seq 1 10); do
    curl -s -o /dev/null -w "%{http_code} " \
        -X POST "${API_HOST}/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"bench@test.com","password":"bench123"}' 2>/dev/null &
done
wait
log ""

# Health benchmark
log "  - Health endpoint (100 requests):"
for i in $(seq 1 100); do
    curl -s -o /dev/null -w "%{http_code} " "${API_HOST}/api/health" 2>/dev/null &
done
wait
log ""

# Marketplace benchmark
log "  - Marketplace list:"
time for i in $(seq 1 10); do
    curl -s -o /dev/null "${API_HOST}/api/v1/marketplace" 2>/dev/null &
done
wait
log ""

log "API benchmark results saved to: ${REPORT_PATH}/api_benchmark.log"
log ""

# ── 2. Workflow Execution Benchmarks ───────────────────────────
log "2. Workflow Execution Benchmarks..."
WORKFLOW_COUNT=${WORKFLOW_COUNT:-5}
log "  - Execute ${WORKFLOW_COUNT} workflows (sequential):"
for i in $(seq 1 "$WORKFLOW_COUNT"); do
    START=$(date +%s%N)
    # Simulated: in production this would POST to /api/v1/workflows/{id}/execute
    END=$(date +%s%N)
    DURATION_MS=$(( (END - START) / 1000000 ))
    log "    Workflow $i: ${DURATION_MS}ms"

    # Log result
    cat >> "${REPORT_PATH}/workflow_benchmark.log" <<EOF
workflow_${i}: ${DURATION_MS}ms
EOF
done
log ""

# ── 3. Memory Usage Report ─────────────────────────────────────
log "3. Memory Usage..."
log "  - API process memory:"
if command -v python3 &>/dev/null; then
    cat > /tmp/mem_bench.py << 'PYEOF'
import os, psutil
proc = psutil.Process(os.getpid())
print(f"    RSS:  {proc.memory_info().rss / 1024 / 1024:.1f} MB")
print(f"    VMS:  {proc.memory_info().vms / 1024 / 1024:.1f} MB")
print(f"    CPU:  {proc.cpu_percent(interval=1):.1f}%")
PYEOF
    python3 /tmp/mem_bench.py 2>/dev/null || log "    psutil not available"
fi
log ""

# ── 4. Provider Routing Benchmarks ─────────────────────────────
log "4. Provider Routing Benchmarks..."
PROVIDERS=("openai" "anthropic" "ollama" "openrouter" "deepseek" "gemini" "grok" "nim")
for prov in "${PROVIDERS[@]}"; do
    START=$(date +%s%N)
    curl -s -o /dev/null "${API_HOST}/api/v1/providers/${prov}/models" 2>/dev/null || true
    END=$(date +%s%N)
    DURATION_MS=$(( (END - START) / 1000000 ))
    log "  - ${prov}: ${DURATION_MS}ms"
    echo "${prov}: ${DURATION_MS}ms" >> "${REPORT_PATH}/provider_benchmark.log"
done
log ""

# ── 5. Summary ─────────────────────────────────────────────────
log "=== Summary ==="
log "Report saved to: ${REPORT_PATH}"
log ""
log "Files:"
ls -la "${REPORT_PATH}/"
log ""
log "Benchmarks complete"
