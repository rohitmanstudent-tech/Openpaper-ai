#!/usr/bin/env bash
# OpenPaper AI — Backup Script (PostgreSQL + Redis + Qdrant)
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/openpaper_backup_${TIMESTAMP}"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-openpaper}"
POSTGRES_USER="${POSTGRES_USER:-openpaper}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-openpaper_secret}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6334}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }

mkdir -p "$BACKUP_PATH"
log "Starting backup to: $BACKUP_PATH"

# ── PostgreSQL ────────────────────────────────────────────────────
log "Backing up PostgreSQL..."
export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -F c \
    -f "${BACKUP_PATH}/postgres.dump" \
    --verbose 2>>"$LOG_FILE"
unset PGPASSWORD
log "PostgreSQL backup complete: $(wc -c < "${BACKUP_PATH}/postgres.dump") bytes"

# ── Redis ─────────────────────────────────────────────────────────
log "Backing up Redis..."
REDIS_DUMP=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG GET dir 2>/dev/null | tail -1 || echo "/data")
if [ -n "$REDIS_DUMP" ]; then
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SAVE 2>>"$LOG_FILE" && \
    cp "${REDIS_DUMP}/dump.rdb" "${BACKUP_PATH}/redis.rdb" 2>/dev/null && \
    log "Redis backup complete" || log "Redis backup skipped (SAVE only)"
fi

# ── Qdrant ────────────────────────────────────────────────────────
log "Backing up Qdrant (if available)..."
if command -v curl &>/dev/null; then
    AUTH=""
    [ -n "$QDRANT_API_KEY" ] && AUTH="-H api-key: $QDRANT_API_KEY"
    SNAPSHOT_RESP=$(curl -s -X POST "$AUTH" "http://${QDRANT_HOST}:6333/snapshots" 2>/dev/null || echo '{"error":"unreachable"}')
    if echo "$SNAPSHOT_RESP" | grep -q '"error"'; then
        log "Qdrant snapshot API unreachable — skipping"
    else
        SNAPSHOT_NAME=$(echo "$SNAPSHOT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('name',''))" 2>/dev/null || echo "")
        if [ -n "$SNAPSHOT_NAME" ]; then
            curl -s -o "${BACKUP_PATH}/qdrant_${SNAPSHOT_NAME}" "$AUTH" "http://${QDRANT_HOST}:6333/snapshots/${SNAPSHOT_NAME}" 2>>"$LOG_FILE"
            log "Qdrant snapshot saved: $SNAPSHOT_NAME"
        fi
    fi
else
    log "curl not found — Qdrant backup skipped"
fi

# ── Environment & Metadata ────────────────────────────────────────
log "Saving metadata..."
cat > "${BACKUP_PATH}/backup_info.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "1.0.0",
  "components": ["postgres", "redis", "qdrant"],
  "files": {
    "postgres": "postgres.dump",
    "redis": "redis.rdb",
    "metadata": "backup_info.json"
  }
}
EOF

# ── Archive ───────────────────────────────────────────────────────
log "Creating archive..."
cd "$BACKUP_DIR"
ARCHIVE="openpaper_backup_${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE" "openpaper_backup_${TIMESTAMP}/" 2>>"$LOG_FILE"
rm -rf "openpaper_backup_${TIMESTAMP}"
log "Backup complete: ${BACKUP_DIR}/${ARCHIVE} ($(wc -c < "$ARCHIVE") bytes)"

# ── Cleanup old backups (keep last 7) ─────────────────────────────
log "Cleaning up backups older than 7 days..."
find "$BACKUP_DIR" -name "openpaper_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
log "Done"
