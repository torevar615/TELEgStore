#!/bin/bash

# Backup script for Docker volumes and data
# Run this script to backup your data before major changes

echo "Creating backup of Docker volumes..."

# Create backup directory with timestamp
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
docker-compose exec postgres pg_dump -U torevar telegramdb > "$BACKUP_DIR/database_backup.sql"

# Backup Docker volumes
echo "Backing up Docker volumes..."
docker run --rm -v telegram_bot_postgres_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
docker run --rm -v telegram_bot_app_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/app_data.tar.gz -C /data .
docker run --rm -v telegram_bot_static_files:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/static_files.tar.gz -C /data .

echo "Backup completed in directory: $BACKUP_DIR"
echo "To restore, use the docker-restore.sh script"