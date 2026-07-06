#!/bin/bash
# ============================================================
# Database Health Check Script
# ============================================================
# Checks PostgreSQL database connection and basic health

set -e

# Configuration
DB_USER="${DB_USER:-krishiuser}"
DB_NAME="${DB_NAME:-krishisathi}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "============================================================"
echo "Database Health Check"
echo "============================================================"
echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Check connection
echo "Checking database connection..."
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ Connection successful"
else
    echo "✗ Connection failed"
    exit 1
fi

# Check database size
echo ""
echo "Database Size:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Check number of tables
echo ""
echo "Tables:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"

# Check connections
echo ""
echo "Active Connections:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE datname = current_database();"

# Check for bloat
echo ""
echo "Database Health Status:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
    SELECT 
        CASE 
            WHEN last_vacuum IS NULL THEN '⚠ Never vacuumed'
            WHEN age(now(), last_vacuum) > '30 days'::interval THEN '⚠ Last vacuum > 30 days ago'
            ELSE '✓ Vacuum up to date'
        END as vacuum_status,
        CASE
            WHEN age(now(), last_autovacuum) > '7 days'::interval THEN '⚠ Last autovacuum > 7 days ago'
            ELSE '✓ Autovacuum up to date'
        END as autovacuum_status,
        n_dead_tup as dead_tuples
    FROM pg_stat_user_tables
    LIMIT 1;
EOF

echo ""
echo "============================================================"
echo "Health Check Completed"
echo "============================================================"
