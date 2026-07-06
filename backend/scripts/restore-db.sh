#!/bin/bash
# ============================================================
# Database Restore Script
# ============================================================
# Restores PostgreSQL database from a backup file

set -e

# Configuration
DB_USER="${DB_USER:-krishiuser}"
DB_NAME="${DB_NAME:-krishisathi}"
DB_HOST="${DB_HOST:-localhost}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="restore_$TIMESTAMP.log"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: ./restore-db.sh <backup-file>"
    echo ""
    echo "Examples:"
    echo "  ./restore-db.sh backups/krishisathi_backup_20240101_120000.sql"
    echo "  ./restore-db.sh backups/krishisathi_backup_20240101_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

{
    echo "============================================================"
    echo "Database Restore Started: $(date)"
    echo "============================================================"
    echo "Database: $DB_NAME"
    echo "Host: $DB_HOST"
    echo "Backup File: $BACKUP_FILE"
    echo ""

    # Confirm restore
    echo "⚠ WARNING: This will overwrite the current database!"
    echo "Database: $DB_HOST/$DB_NAME"
    echo ""
    read -p "Are you sure? Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled"
        exit 0
    fi

    echo ""
    echo "Starting restore..."

    # Handle gzipped files
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        echo "Decompressing backup file..."
        gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --no-password
    else
        PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --no-password \
            < "$BACKUP_FILE"
    fi

    if [ $? -eq 0 ]; then
        echo "✓ Restore completed successfully"
    else
        echo "✗ Restore failed"
        exit 1
    fi

    echo ""
    echo "============================================================"
    echo "Database Restore Completed: $(date)"
    echo "============================================================"

} | tee "$LOG_FILE"

# Print final status
echo ""
echo "Restore log saved to: $LOG_FILE"
