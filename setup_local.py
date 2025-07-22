#!/usr/bin/env python3
"""
Setup script for local development
Run this to install dependencies and set up the database
"""
import subprocess
import sys
import os

def install_packages():
    """Install required Python packages"""
    packages = [
        'python-telegram-bot==20.7',
        'flask==3.0.0',
        'flask-sqlalchemy==3.1.1',
        'psycopg2-binary==2.9.9',
        'python-dotenv==1.0.0',
        'gunicorn==21.2.0'
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("Creating .env file template...")
        with open('.env', 'w') as f:
            f.write("""TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_ID=279005522
DATABASE_URL=postgresql://username:password@localhost/telegramdb
SESSION_SECRET=your_secret_key_here
""")
        print("✓ Created .env file template - please update with your values")
    else:
        print("✓ .env file exists")

def main():
    print("Setting up Telegram Bot for local development...")
    install_packages()
    check_env_file()
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Update .env file with your actual values")
    print("2. Make sure PostgreSQL is running")
    print("3. Create database: psql -c 'CREATE DATABASE telegramdb;'")
    print("4. Run the bot: python standalone_bot.py")

if __name__ == "__main__":
    main()