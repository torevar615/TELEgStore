#!/bin/bash

# Restore script for Docker volumes and data
# Usage: ./docker-restore.sh backup_20241216_143022

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_directory>"
    echo "Available backups:"
    ls -d backup_* 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory $BACKUP_DIR not found!"
    exit 1
fi

echo "Restoring from backup: $BACKUP_DIR"

# Stop containers
echo "Stopping containers..."
docker-compose down

# Restore PostgreSQL database
if [ -f "$BACKUP_DIR/database_backup.sql" ]; then
    echo "Restoring PostgreSQL database..."
    docker-compose up -d postgres
    sleep 10
    docker-compose exec -T postgres psql -U torevar -d telegramdb < "$BACKUP_DIR/database_backup.sql"
fi

# Restore Docker volumes
if [ -f "$BACKUP_DIR/postgres_data.tar.gz" ]; then
    echo "Restoring postgres data..."
    docker run --rm -v telegram_bot_postgres_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
fi

if [ -f "$BACKUP_DIR/app_data.tar.gz" ]; then
    echo "Restoring app data..."
    docker run --rm -v telegram_bot_app_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar xzf /backup/app_data.tar.gz -C /data
fi

if [ -f "$BACKUP_DIR/static_files.tar.gz" ]; then
    echo "Restoring static files..."
    docker run --rm -v telegram_bot_static_files:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar xzf /backup/static_files.tar.gz -C /data
fi

# Start all services
echo "Starting all services..."
docker-compose up -d

echo "Restore completed!"
echo "Your categories, files, and subscribers should be restored."