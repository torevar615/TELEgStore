@echo off
echo Cleaning up Docker networks and containers...

REM Stop and remove all containers
docker-compose down --remove-orphans

REM Remove the problematic network
docker network prune -f

REM Remove unused volumes
docker volume prune -f

REM Restart Docker Desktop (this requires manual action)
echo.
echo Please restart Docker Desktop manually, then run:
echo docker-compose up -d

pause