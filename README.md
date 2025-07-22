# Railway Deployment Guide

## Quick Setup for Railway

### 1. Environment Variables Required

Set these in your Railway project settings:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_ID=279005522
SESSION_SECRET=your_random_secret_key
DATABASE_URL=provided_by_railway_postgres
```

### 2. Add PostgreSQL Database

1. Go to your Railway project
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway will automatically set the `DATABASE_URL` environment variable

### 3. Deploy Steps

1. Connect your GitHub repository to Railway
2. Railway will automatically detect Python and install dependencies
3. Set the environment variables above
4. Deploy will start automatically

### 4. Common Issues

**Bot Token Error**: Make sure your `TELEGRAM_BOT_TOKEN` is set correctly in Railway environment variables

**Database Connection**: Ensure PostgreSQL service is running and `DATABASE_URL` is set

**Admin Access**: Set `ADMIN_ID=279005522` for admin panel access

### 5. Bot Configuration

After deployment, configure your bot with @BotFather:
- Disable "Group Privacy" so users can interact with the bot
- Set bot commands if needed

### 6. Access Your Application

- Web Admin Panel: `https://your-app.railway.app`
- Bot: Start conversation with your bot on Telegram

## File Structure

- `start_services.py` - Main entry point that starts both web app and bot
- `standalone_bot.py` - Telegram bot service
- `main.py` - Flask web application
- `models.py` - Database models
- `routes.py` - Web admin panel routes



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
