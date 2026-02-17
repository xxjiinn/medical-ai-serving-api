# Multi-stage build for smaller image size

# Stage 1: Build stage
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies (for cryptography, PyMySQL, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    cargo \
    rustc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Update PATH to include local Python packages
ENV PATH=/root/.local/bin:$PATH

# Expose port (Railway auto-assigns PORT env var)
ENV PORT=5001
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os, requests; requests.get(f'http://localhost:{os.getenv(\"PORT\", 5001)}/health')" || exit 1

# Run with gunicorn for production
# Railway will override PORT via environment variable
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 run:app
