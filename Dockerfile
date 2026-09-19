# Use lightweight base
FROM python:3.12-slim

# Prevent Python from writing .pyc files & buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg is required)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies separately for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run app
CMD ["python", "bot.py"]
