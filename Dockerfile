FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY local_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directory for file storage
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Default command (can be overridden in docker-compose)
CMD ["python", "standalone_bot.py"]