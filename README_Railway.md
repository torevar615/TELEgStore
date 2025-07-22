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