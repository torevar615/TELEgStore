# Telegram File Bot - Docker Setup

## Quick Start with Docker

### Prerequisites
- Docker Desktop installed on your PC
- Git (optional, for cloning)

### Steps to Run

1. **Download all project files** to your local directory:
   ```
   C:\Users\torevar\Desktop\proejct\telegrambot\
   ```

2. **Copy these files from this project:**
   - `Dockerfile`
   - `docker-compose.yml`
   - `standalone_bot.py`
   - `models.py`
   - `app.py`
   - `routes.py`
   - `local_requirements.txt`
   - `templates/` folder (all HTML files)
   - `static/` folder (CSS/JS files)

3. **Start the services:**
   ```cmd
   cd C:\Users\torevar\Desktop\proejct\telegrambot
   docker-compose up -d
   ```

4. **Access the services:**
   - **Web Admin Panel:** http://localhost:5000
   - **Telegram Bot:** Already running and responding to messages
   - **Database:** PostgreSQL on localhost:5432

### What Docker Compose Includes

- **PostgreSQL Database:** Automatic setup with your credentials
- **Web Interface:** Admin panel for managing categories
- **Telegram Bot:** Standalone service responding to messages
- **Persistent Storage:** Database data saved between restarts

### Environment Variables (Already Configured)

```
DATABASE_URL=postgresql://torevar:hesoyam@postgres:5432/telegramdb
TELEGRAM_BOT_TOKEN=7961338599:AAEGSHwGMycf8oRSwFd5ZvW-3u72MDW4aHE
ADMIN_ID=279005522
SESSION_SECRET=docker_secret_key_2024
```

### Useful Commands

```cmd
# Start services
docker-compose up -d

# View logs
docker-compose logs bot
docker-compose logs web

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View database
docker-compose exec postgres psql -U torevar -d telegramdb
```

### Troubleshooting

- If port 5000 is busy: Change `"5000:5000"` to `"5001:5000"` in docker-compose.yml
- If port 5432 is busy: Change `"5432:5432"` to `"5433:5432"` in docker-compose.yml
- View logs: `docker-compose logs`