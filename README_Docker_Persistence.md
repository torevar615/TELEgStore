# Docker Persistent Storage Guide

## What's Now Persistent

Your Docker setup now saves all data permanently on your local machine:

✓ **Database** - All categories, files, and subscribers
✓ **Application Data** - Settings and configurations  
✓ **Static Files** - Uploaded assets and media

## Benefits

- **Container Safe**: Delete containers without losing data
- **Restart Safe**: Reboot your computer and keep everything
- **Update Safe**: Pull new code versions while preserving data
- **Backup Ready**: Easy data backup and restore

## How It Works

Docker volumes store your data outside containers:
- `postgres_data` - Database files
- `app_data` - Application data folder
- `static_files` - Uploaded files and assets

## Commands

**Start with persistent storage:**
```bash
docker-compose up -d
```

**View your data volumes:**
```bash
docker volume ls
```

**Backup everything:**
```bash
./docker-backup.sh
```

**Restore from backup:**
```bash
./docker-restore.sh backup_20241216_143022
```

**Clean restart (keeps data):**
```bash
docker-compose down
docker-compose up -d
```

**Complete reset (deletes all data):**
```bash
docker-compose down -v
docker volume prune
```

## Data Location

Your persistent data is stored in Docker volumes on your local machine. Even if you:
- Delete containers: `docker-compose down`
- Remove images: `docker image prune`
- Update code: `git pull`

Your categories, files, and subscribers remain intact.

## Backup Schedule

Run backup weekly or before major changes:
```bash
./docker-backup.sh
```

This creates timestamped backups you can restore anytime.