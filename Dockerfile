# Multi-stage build for smaller image size

# Stage 1: Build stage
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies (only for cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
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
EXPOSE 5001

# Run with gunicorn for production
# Use shell form with explicit sh -c for environment variable expansion
CMD sh -c "gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --threads 2 --timeout 120 run:app"
