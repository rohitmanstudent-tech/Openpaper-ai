#!/usr/bin/env bash
# OpenPaper AI — One-Click Restore Script
set -euo pipefail

RESTORE_FILE="${1:-}"
LOG_DIR="./restore_logs"

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

log() { echo "[$(date +%H:%M:%S)] $*"; }

if [ -z "$RESTORE_FILE" ]; then
    echo "Usage: $0 <backup-file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -1t ./backups/openpaper_backup_*.tar.gz 2>/dev/null || echo "  (no backups found in ./backups/)"
    exit 1
fi

if [ ! -f "$RESTORE_FILE" ]; then
    log "ERROR: Backup file not found: $RESTORE_FILE"
    exit 1
fi

mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/restore_${TIMESTAMP}.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

RESTORE_DIR=$(mktemp -d)
trap 'rm -rf "$RESTORE_DIR"' EXIT

log "=== OpenPaper Restore ==="
log "Restoring from: $RESTORE_FILE"
log ""

# ── Extract ───────────────────────────────────────────────────────
log "Extracting backup archive..."
tar -xzf "$RESTORE_FILE" -C "$RESTORE_DIR"
BACKUP_CONTENT_DIR=$(find "$RESTORE_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
log "Extracted to: $BACKUP_CONTENT_DIR"

# ── Validate ──────────────────────────────────────────────────────
if [ ! -f "${BACKUP_CONTENT_DIR}/backup_info.json" ]; then
    log "ERROR: Invalid backup — missing backup_info.json"
    exit 1
fi

BACKUP_VERSION=$(python3 -c "import json; d=json.load(open('${BACKUP_CONTENT_DIR}/backup_info.json')); print(d.get('version','?'))" 2>/dev/null || echo "?")
log "Backup version: $BACKUP_VERSION"
log ""

# ── Confirm ───────────────────────────────────────────────────────
echo "WARNING: This will OVERWRITE existing data!"
echo "  - PostgreSQL database: $POSTGRES_DB"
echo "  - Redis database on $REDIS_HOST:$REDIS_PORT"
echo "  - Qdrant collections"
echo ""
read -rp "Continue? (type 'yes' to proceed): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled"
    exit 0
fi
log ""

# ── PostgreSQL Restore ────────────────────────────────────────────
if [ -f "${BACKUP_CONTENT_DIR}/postgres.dump" ]; then
    log "Restoring PostgreSQL..."
    export PGPASSWORD="$POSTGRES_PASSWORD"
    pg_restore \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c \
        --if-exists \
        "${BACKUP_CONTENT_DIR}/postgres.dump" || log "WARNING: pg_restore had errors (may be expected)"
    unset PGPASSWORD
    log "PostgreSQL restore complete"
else
    log "Skipping PostgreSQL (no dump found)"
fi

# ── Redis Restore ─────────────────────────────────────────────────
if [ -f "${BACKUP_CONTENT_DIR}/redis.rdb" ]; then
    log "Restoring Redis..."

    REDIS_DUMP_DIR=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG GET dir 2>/dev/null | tail -1 || echo "/data")

    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SHUTDOWN NOSAVE 2>/dev/null || true
    sleep 1

    cp "${BACKUP_CONTENT_DIR}/redis.rdb" "${REDIS_DUMP_DIR}/dump.rdb"

    redis-server --daemonize yes 2>/dev/null || true
    sleep 1

    log "Redis restore complete"
else
    log "Skipping Redis (no dump found)"
fi

# ── Qdrant Restore ────────────────────────────────────────────────
QDRANT_SNAPSHOT=$(ls "${BACKUP_CONTENT_DIR}"/qdrant_* 2>/dev/null | head -1 || echo "")
if [ -n "$QDRANT_SNAPSHOT" ]; then
    log "Restoring Qdrant from: $(basename "$QDRANT_SNAPSHOT")"
    if command -v curl &>/dev/null; then
        AUTH=""
        [ -n "$QDRANT_API_KEY" ] && AUTH="-H api-key: $QDRANT_API_KEY"
        SNAPSHOT_NAME=$(basename "$QDRANT_SNAPSHOT")
        UPLOAD_RESP=$(curl -s -X POST "$AUTH" \
            -F "snapshot=@${QDRANT_SNAPSHOT}" \
            "http://${QDRANT_HOST}:6333/snapshots/upload" 2>/dev/null || echo '{"error":"unreachable"}')
        if echo "$UPLOAD_RESP" | grep -q '"error"'; then
            log "Qdrant restore skipped — API unreachable"
        else
            log "Qdrant snapshot uploaded"
        fi
    fi
else
    log "Skipping Qdrant (no snapshot found)"
fi

log ""
log "=== Restore Complete ==="
log "Log file: $LOG_FILE"
