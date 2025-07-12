# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies that are imported in main.py
RUN pip install --no-cache-dir \
    requests \
    pyfiglet \
    colorama \
    telethon \
    pytz

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (if needed for web interface)
EXPOSE 5000

# Set the default command
CMD ["python", "main.py"]