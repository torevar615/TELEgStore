@echo off
echo Starting Docker containers with legacy build...

REM Set environment variables to disable buildx
set DOCKER_BUILDKIT=0
set COMPOSE_DOCKER_CLI_BUILD=0

REM Stop any running containers
docker-compose down

REM Start with rebuild
docker-compose up -d --build

echo.
echo Containers started! 
echo Web app: http://localhost:5000
echo.
echo Check logs:
echo docker-compose logs web
echo docker-compose logs bot
echo.
echo Don't forget to add your bot token to .env file!

pause