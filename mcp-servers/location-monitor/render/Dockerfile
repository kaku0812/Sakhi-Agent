# Dockerfile for Sakhi Location Monitor API
# Deploy to Render as a Docker web service

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements_render.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_render.txt

# Copy application code
COPY app_render.py .

# Expose port (Render uses PORT env variable)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn app_render:app --host 0.0.0.0 --port ${PORT:-8000}"]
