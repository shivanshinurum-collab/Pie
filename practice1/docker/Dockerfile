FROM python:3.11-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (build-essential and libpq-dev for Postgres, ffmpeg for MoviePy video processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ /app/src/

# Create directory for storage
RUN mkdir -p /app/storage

EXPOSE 8000

# Default command can be overridden by docker-compose
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
