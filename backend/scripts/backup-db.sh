#!/bin/bash
# ============================================================
# Database Backup Script
# ============================================================
# Performs full backup of PostgreSQL database

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-.}"
DB_USER="${DB_USER:-krishiuser}"
DB_NAME="${DB_NAME:-krishisathi}"
DB_HOST="${DB_HOST:-localhost}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/krishisathi_backup_$TIMESTAMP.sql"
LOG_FILE="$BACKUP_DIR/backup_$TIMESTAMP.log"

{
    echo "============================================================"
    echo "Database Backup Started: $(date)"
    echo "============================================================"
    echo "Database: $DB_NAME"
    echo "Host: $DB_HOST"
    echo "Backup File: $BACKUP_FILE"
    echo ""

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    # Perform backup
    echo "Starting backup..."
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        > "$BACKUP_FILE"; then
        
        # Compress the backup
        gzip "$BACKUP_FILE"
        BACKUP_FILE="$BACKUP_FILE.gz"
        
        echo "✓ Backup completed successfully"
        echo "File: $BACKUP_FILE"
        ls -lh "$BACKUP_FILE"
    else
        echo "✗ Backup failed"
        exit 1
    fi

    # Cleanup old backups (keep last 30 days)
    echo ""
    echo "Cleaning up old backups (older than 30 days)..."
    find "$BACKUP_DIR" -name "krishisathi_backup_*.sql.gz" -mtime +30 -delete
    echo "✓ Cleanup completed"

    echo ""
    echo "============================================================"
    echo "Database Backup Completed: $(date)"
    echo "============================================================"

} | tee "$LOG_FILE"

# Print final status
echo ""
echo "Backup log saved to: $LOG_FILE"
